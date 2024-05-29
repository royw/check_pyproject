"""
Check that [project] and [tool.poetry] tables are in-sync in the pyproject.toml file.

The Python Packaging User Guide now specifies pyproject.toml metadata.

Poetry <2.0 predates the metadata specification and instead used the then current standard of
[tool.poetry] table.  While there is a lot of overlap, there are some differences (ex. dependency package specifiers).
Poetry 2.0 will support PyPA pyproject.toml specification (formerly PEP 621) which will obsolete
this utility.

So if your project uses poetry and any other tool that requires the current pyproject.toml metadata, or you
are prepping for Poetry 2.0 and do not want to use
then you need to manually maintain sync between [project] and [tool.poetry] tables.

This tool checks that overlapping metadata, between [project] and [tool.poetry] tables, is roughly in-sync.

- The Python Packaging User Guide can be found here: https://packaging.python.org/en/latest
- The pyproject.toml specification can be found here: https://pypi.python.org/pypi/pyproject.toml
- The Poetry pyproject.toml metadata can be found here: https://python-poetry.org/docs/pyproject
"""

import re
import sys
import tomllib
from pathlib import Path
from pprint import pformat
from typing import Callable, Any
from loguru import logger
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version


def bump_major_version(version: Version) -> Version:
    """
    Increment the major version by 1 and zeroing the minor and patch versions and removing any pre,
    post, development, or local segments.  Preserves the epoch.
    """
    epoch_str = f"{version.epoch}!" if version.epoch else ""
    major = 0
    if len(version.release) >= 1:
        major = version.release[0]
    return Version(f"{epoch_str}{major + 1}.0.0")


def bump_minor_version(version: Version) -> Version:
    """
    Increment the minor version by 1 and zeroing the patch version and removing any pre,
    post, development, or local segments.  Preserves the epoch and major version.
    """
    epoch_str = f"{version.epoch}!" if version.epoch else ""
    major: int = 0
    minor: int = 0
    if len(version.release) >= 1:
        major = version.release[0]
    if len(version.release) >= 2:
        minor = version.release[1]
    return Version(f"{epoch_str}{major}.{minor + 1}.0")


def bump_patch_version(version: Version) -> Version:
    """
    Increment the patch (micro) version by 1 and removing any pre, post, development,
    or local segments.  Preserves the epoch and major version.
    """
    epoch_str = f"{version.epoch}!" if version.epoch else ""
    major: int = 0
    minor: int = 0
    patch: int = 0
    if len(version.release) >= 1:
        major = version.release[0]
    if len(version.release) >= 2:
        minor = version.release[1]
    if len(version.release) >= 3:
        patch = version.release[2]
    return Version(f"{epoch_str}{major}.{minor}.{patch + 1}")


def max_version(version_str: str) -> Version:
    """
    Increment the version number to the upper bound of the version.
    Examples:
        "1.2.4" will be bumped to "2.0.0"
        "0.1.2" will be bumped to "0.2.0"
        "0.0.7" will be bumped to "0.0.8"
        "0 will bump to "1.0.0"
        "0.0 will bump to "0.1.0"
        "0.0.0 will bump to "0.1.0"
    """
    ver: Version = Version(version_str)
    if ver.major:
        ver = bump_major_version(ver)
    elif ver.minor:
        ver = bump_minor_version(ver)
    elif ver.micro:
        ver = bump_patch_version(ver)
    else:
        # 0 or 0.0 or 0.0.0
        if len(ver.release) == 1:
            # 0 bumping to 1
            ver = bump_major_version(ver)
        else:
            # 0.0 bumping to 0.1
            # and special case of 0.0.0 bumping to 0.1.0
            ver = bump_minor_version(ver)
    return ver


def fill_version_to_three_parts(version_str: str) -> str:
    """
    Fill out requirement to at least 3 parts, ex: 1.2 => 1.2.0
    """
    if not version_str:
        return "0.0.0"
    while len(version_str.split(".")) < 3:
        version_str += ".0"
    return version_str


def caret_requirement_to_pep508(specification: str, max_bounds: bool = True) -> str:
    """
    Caret requirements allow SemVer compatible updates to a specified version. An update is allowed if the
    new version number does not modify the left-most non-zero digit in the major, minor, patch grouping.

    By default, an upper bound will be generated (ex:  "^1.2.3" becomes ">=1.2.3,<2.0.0").
    To disable this behavior, set max_bounds to False (ex:  "^1.2.3" becomes ">=1.2.3").
    """
    if max_bounds:
        return str(
            SpecifierSet(
                f">={fill_version_to_three_parts(specification)}, "
                f"<{fill_version_to_three_parts(str(max_version(specification)))}"
            )
        )
    else:
        return str(SpecifierSet(f">={fill_version_to_three_parts(specification)}"))


def tilde_requirement_to_pep508(specification: str) -> str:
    """
    Tilde requirements specify a minimal version with some ability to update. If you specify a major, minor,
    and patch version or only a major and minor version, only patch-level changes are allowed. If you only
    specify a major version, then minor- and patch-level changes are allowed.

    examples:
      "~1.2.3" becomes ">=1.2.3,<1.3.0"
      "~1.2" becomes ">=1.2.0, <1.3.0"
      "~1" becomes ">=1.0.0, <2.0.0")
    """
    ver: Version = Version(specification)
    if len(ver.release) == 1:
        ver = bump_major_version(ver)
    else:
        ver = bump_minor_version(ver)
    return str(
        SpecifierSet(f">={fill_version_to_three_parts(specification)}, " f" <{fill_version_to_three_parts(str(ver))}")
    )


def wildcard_requirement_to_pep508(specification: str) -> str:
    """
    Wildcard requirements allow for the latest (dependency dependent) version where the wildcard
    is positioned. *, 1.* and 1.2.* are examples of wildcard requirements.

    examples:
    "*" becomes ">=0.0.0"
    "1*" becomes ">=1.0.0, <2.0.0"
    "1.2.*" becomes ">=1.2.0, <1.3.0"
    """
    if specification == "*":
        return str(SpecifierSet(f">={fill_version_to_three_parts('0')}"))
    else:
        version_string: str = specification.rstrip("*").rstrip(".")  # ex: "1", "1.2"
        ver: Version = Version(version_string)

        match len(ver.release):
            case 1:
                ver = bump_major_version(ver)
            case 2:
                ver = bump_minor_version(ver)

        return str(
            SpecifierSet(
                f">={fill_version_to_three_parts(version_string)}, " f" <{fill_version_to_three_parts(str(ver))}"
            )
        )


def convert_poetry_to_pep508(value: str, max_bounds=True) -> str:
    """
    Convert poetry dependency specifiers (^v.v, ~ v.v, v.*, <=v, > v, != v) to pep508 format
    returns a string containing comma separated pep508 specifiers
    """
    out: list[str] = []
    value = re.sub(r"([\^~<>=!]+)\s+", r"\1", value)
    requirement: str
    for requirement in re.split(r",\s*", value):
        # ^a.b.c
        if requirement.startswith("^"):
            out.append(caret_requirement_to_pep508(requirement[1:], max_bounds))
        elif requirement.startswith("~"):
            out.append(tilde_requirement_to_pep508(requirement[1:]))
        elif "*" in requirement:
            out.append(wildcard_requirement_to_pep508(requirement))
        else:
            out.append(str(SpecifierSet(fill_version_to_three_parts(requirement))))
    return ",".join(out)


def project_dependency_fields(out: set[Requirement], values: list[str]) -> None:
    """
    Convert list of pep508 strings to a set of packaging requirements
    """
    for value in values:
        out.add(Requirement(value))


def poetry_optional_requirements(out: set[Requirement], key: str, value: dict[str, str]) -> None:
    """
    Optional dependency
    """
    if "version" in value and "optional" in value:
        if value["optional"].strip('"').lower() == "true":
            out.add(Requirement(f"{key}{str(convert_poetry_to_pep508(value['version']))}"))


def poetry_extra_requirements(out: set[Requirement], key: str, value: dict[str, str]) -> None:
    """
    Extra dependency
    """
    if "version" in value and "extra" in value:
        extra: str | list[str] = value["extra"]
        if isinstance(extra, list):
            extra = ",".join(extra)
        out.add(Requirement(f"{key}[{extra}]{str(convert_poetry_to_pep508(value['version']))}"))


def poetry_dependency_fields(out: set[Requirement], value: dict[str, dict[str, str]]) -> None:
    """
    There is a special case where the required python version is in different locations:
    project.requires-python and tool.poetry.dependencies.python.  So for poetry dependencies
    we skip "python" and handle the special case elsewhere.

    We also have to handle optional and extra dependencies.
    From [Extras](https://python-poetry.org/docs/pyproject/#extras):

        [tool.poetry.dependencies]
        # These packages are mandatory and form the core of this package’s distribution.
        mandatory = "^1.0"
        pandas = {version="^2.2.1", extras=["computation", "performance"]}

        # A list of all the optional dependencies, some of which are included in the
        # below `extras`. They can be opted into by apps.
        psycopg2 = { version = "^2.9", optional = true }
        mysqlclient = { version = "^1.3", optional = true }

        [tool.poetry.group.dev.dependencies]
        fastapi = {version="^0.92.0", extras=["all"]}

        [tool.poetry.extras]
        mysql = ["mysqlclient"]
        pgsql = ["psycopg2"]
        databases = ["mysqlclient", "psycopg2"]

    So we have to support two value types: str (for mandatory) and dict[str, str] (for optional and extra).
    """
    # should be poetry dependency metadata
    for key, v in value.items():
        if key == "python":
            continue
        if isinstance(v, str):
            # mandatory dependency
            out.add(Requirement(f"{key}{str(convert_poetry_to_pep508(v))}"))
        if isinstance(v, dict):
            poetry_optional_requirements(out, key, v)
            poetry_extra_requirements(out, key, v)


def package_dependency_field(value: set[Requirement] | list[str] | dict[str, str]) -> set[Requirement]:
    """
    Callback to convert a package dependency specifiers into a set of package dependency fields.
    list[str] values should be from the project table and already in pep508 format.
    dict[str, str] should be from the [tool.poetry] table and need conversion to pep508 format.

    returns set of pep508 dependency fields.
    """
    out: set[Requirement] = set()

    if isinstance(value, list):
        project_dependency_fields(out, value)

    if isinstance(value, dict):
        poetry_dependency_fields(out, value)
    return out


def string_field(value: str) -> str:
    """
    Callback to use the value string as is for comparisons
    """
    return value


def set_field(value: list[str]) -> set[str]:
    """
    Callback to convert list of strings to a set of strings for comparing lists
    """
    return set(value)


def author_field(value: list[str] | list[dict[str]]) -> set[str]:
    """
    Callback to convert auther/maintainer fields into project table's format:
    full name <email@example.com>

    returns: set of project table style "user <email>" strings'
    """
    out: set = set()
    if isinstance(value, list):
        for v in value:
            if isinstance(v, str):
                # project table style string, use as is
                out.add(v)
            if isinstance(v, dict):
                # tool.poetry style, convert to project table style
                out.add(f"{v['name']} <{v['email']}>")
    return out


def check_single_field(
    callback: Callable[[Any], str | set[str] | set[Requirement]], field: str, project_data: dict, poetry_data: dict
) -> int:
    """
    Check a field for existence, and equality.
    Returns the number of problems detected.
    """
    number_of_problems: int = 0
    if field in project_data:
        # in project
        if field in poetry_data:
            # in both
            logger.info(f'"{field}" found in both [project] and [tool.poetry]')
            if callback(project_data[field]) != callback(poetry_data[field]):
                # values don't equal
                logger.error(
                    f'Values do not match between project.{field}: "{project_data[field]}" '
                    f'and tool.poetry.{field}: "{poetry_data[field]}"'
                )
                number_of_problems = 1
        else:
            # not in tool.poetry, so in project only
            logger.warning(f'[project].{field}: "{project_data[field]}", but "{field}" not in [tool.poetry].')
            number_of_problems = 1
    else:
        # not in project
        if field in poetry_data:
            # in tool.poetry only
            logger.warning(f'[tool.poetry].{field}: "{poetry_data[field]}", but "{field}" not in [project].')
            number_of_problems = 1
        else:
            # in neither
            logger.warning(f'"{field}" not found in [project] nor in [tool.poetry]')
    return number_of_problems


def check_fields(
    callback: Callable[[Any], str | set[str] | set[Requirement]], fields: list, toml_data: dict[str, Any]
) -> int:
    """
    Check the fields for existence, and equality.
    Returns the number of problems detected
    """
    number_of_problems: int = 0

    for field in fields:
        number_of_problems += check_single_field(callback, field, toml_data["project"], toml_data["tool"]["poetry"])

    return number_of_problems


def check_asymmetric_fields(
    callback: Callable[[Any], str | set[str] | set[Requirement]], field_dict: dict, toml_data: dict[str, Any]
) -> int:
    """
    Check fields that differ in table names between project and tool.poetry.
    Project uses: optional-dependencies.{key} while poetry uses: group.{key}.dependencies
    Returns the number of problems detected.
    """

    number_of_problems: int = 0

    # project_data and poetry_data neet to point to the final field's value
    # Example: for field_dict = field_dict = {'poetry': ['group', 'dev', 'dependencies']}
    # poetry_data will end up pointing to toml_data['tool.poetry.group.dev.dependencies']
    project_data: dict[str, Any] = toml_data["project"]
    poetry_data: dict[str, Any] = toml_data["tool"]["poetry"]

    for name in field_dict["project"]:
        project_data = project_data.get(name, {})

    for name in field_dict["poetry"]:
        poetry_data = poetry_data.get(name, {})

    # build the name strings used in logging
    project_name = ".".join(field_dict["project"])
    poetry_name = ".".join(field_dict["poetry"])

    # check the field's values
    if callback(project_data) != callback(poetry_data):
        logger.error(f"[project.{project_name}] does not match poetry.{poetry_name}")
        logger.debug(f"[project] {project_name}:\n{pformat(sorted(project_data))}")
        logger.debug(f"[poetry] {poetry_name}:\n{pformat(package_dependency_field(poetry_data))}")
        number_of_problems += 1
    return number_of_problems


def check_python_version(toml_data: dict[str, Any]) -> int:
    """
    There is a special case where the required python version is in different locations:
    project.requires-python and tool.poetry.dependencies.python.
    Also project.requires-python requires a single predicate like ">=3.11" with no upper bound, i.e.
    ">=3.11, <4.0" is invalid.
    """
    number_of_problems: int = 0

    project_data: dict[str, Any] = toml_data["project"]
    poetry_data: dict[str, Any] = toml_data["tool"]["poetry"]

    if "requires-python" in project_data:
        if "python" in poetry_data["dependencies"]:
            # python is specified in both places, so verify their versions are the same
            project_python_version = convert_poetry_to_pep508(project_data["requires-python"])
            poetry_python_version = convert_poetry_to_pep508(poetry_data["dependencies"]["python"], max_bounds=False)
            if project_python_version != poetry_python_version:
                logger.error(
                    f"project.requires-python ({project_python_version}) "
                    f"does not match tool.poetry.dependencies.python ({poetry_python_version})"
                )
                number_of_problems += 1
        else:
            project_python_version = project_data["requires-python"]
            logger.error(
                f"project.requires-python is {project_python_version} but tool.poetry.dependencies.python is missing."
            )
            number_of_problems += 1
    elif "python" in poetry_data["dependencies"]:
        poetry_python_version = convert_poetry_to_pep508(poetry_data["dependencies"]["python"])
        logger.error(
            f"tool.poetry.dependencies.python is {poetry_python_version} but project.requires-python is missing."
        )
        number_of_problems += 1
    else:
        logger.warning("project.requires and tool.poetry.dependencies.python are missing.")
    return number_of_problems


def check_pyproject_toml(toml_data: dict[str, Any]) -> int:
    """
    Check fields that should be identical between [project] and [tool.poetry]
    returns False if there are problems detected
    """

    number_of_problems: int = 0

    # group field names by the TOML type of their values

    string_field_names: list[str] = ["name", "description", "readme", "version", "scripts", "urls"]
    set_field_names: list[str] = ["keywords", "classifiers"]
    author_field_names: list[str] = ["authors", "maintainers"]
    dependency_field_names: list[str] = ["dependencies"]
    optional_dependency_keys: set[str] = set(toml_data["tool"]["poetry"]["group"]) | set(
        toml_data["project"]["optional-dependencies"]
    )

    # gather all the field names we check, so we can later find the unchecked field names
    checked_field_names: list[str] = (
        string_field_names
        + set_field_names
        + author_field_names
        + dependency_field_names
        + ["optional-dependencies", "group"]
    )

    # check the field values when the field names are the same in project and tool.poetry tables
    number_of_problems += check_fields(string_field, string_field_names, toml_data)
    number_of_problems += check_fields(set_field, set_field_names, toml_data)
    number_of_problems += check_fields(author_field, author_field_names, toml_data)
    number_of_problems += check_python_version(toml_data)
    number_of_field_problems: int = check_fields(package_dependency_field, dependency_field_names, toml_data)
    if number_of_field_problems > 0:
        number_of_problems += number_of_field_problems
        logger.debug(
            "project dependency value(s):\n" + pformat(toml_data["project"]["dependencies"]).replace("'", '"')
        )
        logger.debug(
            "poetry dependency value(s) formated as pep508:\n"
            + pformat(toml_data["tool"]["poetry"]["dependencies"]).replace("'", '"')
        )

    # check the field values when the field names differ between project and tool.poetry tables
    key: str
    for key in optional_dependency_keys:
        field_dict: dict[str, list[str]] = {
            "project": ["optional-dependencies", key],
            "poetry": ["group", key, "dependencies"],
        }
        number_of_problems += check_asymmetric_fields(package_dependency_field, field_dict, toml_data)

    # warn about fields not checked
    logger.warning(f"Fields not checked in [project]:  {sorted(toml_data['project'].keys() - checked_field_names)}")
    logger.warning(
        f"Fields not checked in [tool.poetry]:  {sorted(toml_data['tool']['poetry'].keys() - checked_field_names)}"
    )
    logger.info(
        "Note that the license tables have completely different formats between\n"
        "[project] (takes either a file or a text attribute of the actual license and "
        "[tool.poetry] (takes the name of the license), so both must be manually set."
    )
    return number_of_problems


def validate_pyproject_toml_file(project_filename: Path) -> int:
    """read the pyproject.toml file then cross validate the [project] and [tool.poetry] sections."""
    number_of_problems: int = 0
    try:
        with open(project_filename, "r", encoding="utf-8") as f:
            number_of_problems += check_pyproject_toml(toml_data=tomllib.loads(f.read()))
    except FileNotFoundError:
        logger.error(f'"{project_filename}" is not a file.')
        number_of_problems = 1  # one error
    except IsADirectoryError:
        logger.error(f'"{project_filename}" is a directory, not a pyproject.toml file.')
        number_of_problems = 1  # one error
    except ValueError as err:
        logger.error(f"Unable to parse {project_filename}: {err}")
        number_of_problems = 1  # one error
    logger.info(f"Validate pyproject.toml file: {project_filename} => {number_of_problems} problems detected.")
    return number_of_problems


def main(args: list[str] = None) -> None:  # pragma: no cover
    """main function
    If 1 or more arguments are given, they will be passed to `validate_pyproject_toml_file`.
    Else, `validate_pyproject_toml_file` will be called with `$CWD/pyproject.toml`.
    """
    number_of_problems: int = 0
    if not args:
        args: list[str] = sys.argv[1:]
    if len(args) == 0:
        args.append(str(Path.cwd() / "pyproject.toml"))
    for arg in args:
        logger.info(f'Checking: "{arg}"')
        number_of_problems += validate_pyproject_toml_file(Path(arg))
    exit(number_of_problems)


if __name__ == "__main__":
    main(args=sys.argv[1:])  # pragma: no cover
