"""
Check that [project] and [tool.poetry] tables are in-sync in the pyproject.toml file.

The Python Packaging User Guide now specifies pyproject.toml metadata.

Poetry predates the metadata specification and instead used the then current standard of
[tool.poetry] table.  While there is a lot of overlap, there are some differences (ex. dependency package specifiers).

So if your project uses poetry and any other tool that requires the current pyproject.toml metadata,
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
from packaging.version import Version


def bump_major_version(version: Version) -> Version:
    epoch_str = f"{version.epoch}!" if version.epoch else ""
    major = 0
    if len(version.release) >= 1:
        major = version.release[0]
    return Version(f"{epoch_str}{major + 1}.0.0")


def bump_minor_version(version: Version) -> Version:
    epoch_str = f"{version.epoch}!" if version.epoch else ""
    major: int = 0
    minor: int = 0
    if len(version.release) >= 1:
        major = version.release[0]
    if len(version.release) >= 2:
        minor = version.release[1]
    return Version(f"{epoch_str}{major}.{minor + 1}.0")


def bump_patch_version(version: Version) -> Version:
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


def max_version(version_str: str) -> str:
    """bump the version number to the upper bound of the version.
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
    return str(ver)


def fill_version_to_three_parts(version_str: str) -> str:
    """fill out requirement to at least 3 parts, ex: 1.2 => 1.2.0"""
    if not version_str:
        return "0.0.0"
    while len(version_str.split(".")) < 3:
        version_str += ".0"
    return version_str


def caret_requirement_to_pep508(specification: str, max_bounds: bool) -> str:
    """Caret requirements allow SemVer compatible updates to a specified version. An update is allowed if the
    new version number does not modify the left-most non-zero digit in the major, minor, patch grouping.
    """
    if max_bounds:
        return (
            f">={fill_version_to_three_parts(specification)}, "
            f"<{fill_version_to_three_parts(max_version(specification))}"
        )
    else:
        return f">={fill_version_to_three_parts(specification)}"


def tilde_requirement_to_pep508(specification: str) -> str:
    """Tilde requirements specify a minimal version with some ability to update. If you specify a major, minor,
    and patch version or only a major and minor version, only patch-level changes are allowed. If you only
    specify a major version, then minor- and patch-level changes are allowed.
    """
    ver: Version = Version(specification)
    if len(ver.release) == 1:
        ver = bump_major_version(ver)
    else:
        ver = bump_minor_version(ver)
    return f">={fill_version_to_three_parts(specification)}, <{fill_version_to_three_parts(str(ver))}"


def wildcard_requirement_to_pep508(specification: str) -> str:
    """Wildcard requirements allow for the latest (dependency dependent) version where the wildcard
    is positioned. *, 1.* and 1.2.* are examples of wildcard requirements.
    """
    if specification == "*":
        return f">={fill_version_to_three_parts('0')}"
    else:
        version_string: str = specification.rstrip("*").rstrip(".")  # ex: "1", "1.2"
        ver: Version = Version(version_string)

        match len(ver.release):
            case 1:
                ver = bump_major_version(ver)
            case 2:
                ver = bump_minor_version(ver)

        return f">={fill_version_to_three_parts(version_string)}, <{fill_version_to_three_parts(str(ver))}"


def multiple_requirement_to_pep508(requirement: str) -> str:
    buf = []
    for part in requirement.split(" "):
        if part:
            buf.append(fill_version_to_three_parts(part))
    return " ".join(buf)


def convert_poetry_to_pep508(value: str, max_bounds=True) -> str:
    """convert poetry dependency specifiers(^v.v, ~ v.v, v.*, <=v, > v, != v) to pep508 format
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
            out.append(multiple_requirement_to_pep508(requirement))
    return ", ".join(out)


def project_dependency_fields(value: list[str]):
    out: set = set()
    for v in value:
        if isinstance(v, str):
            # should be pep508 dependency metadata
            out.add(v)
    return out


def poetry_dependency_fields(value: dict[str, str]) -> set[str]:
    # should be poetry dependency metadata
    out: set = set()
    for key, v in value.items():
        if key == "python":
            continue
        if isinstance(v, str):
            out.add(f"{key}{convert_poetry_to_pep508(v)}")
        if isinstance(v, dict):
            if "extras" in v and "version" in v:
                out.add(f"{key}{v['extras']}{convert_poetry_to_pep508(v['version'])}")
    return out


def package_dependency_field(value: list[str] | dict[str, str]) -> set[str]:
    """callback to convert a package dependency specifiers into a set of package dependency fields.
    list[str] values should be from the project table and already in pep508 format.
    dict[str, str] should be from the [tool.poetry] table and need conversion to pep508 format.

    There is a special case where the required python version is in different locations:
    project.requires-python and tool.poetry.dependencies.python.  So for poetry dependencies
    we skip "python" and handle the special case elsewhere.

    returns set of pep508 dependency fields.
    """
    if isinstance(value, list):
        return project_dependency_fields(value)

    if isinstance(value, dict):
        return poetry_dependency_fields(value)


def string_field(value: str) -> str:
    """callback to use the value string as is for comparisons"""
    return value


def set_field(value: list[str]) -> set[str]:
    """callback to convert list of strings to a set of strings for comparing lists"""
    return set(value)


def author_field(value: list[str] | list[dict[str]]) -> set[str]:
    """callback to convert auther/maintainer fields into project table's format:
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


def check_fields(callback: Callable[[Any], str | set[str]], fields: list, toml_data: dict) -> int:
    """check the fields for existence, and equality.
    returns the number of problems detected"""
    number_of_errors: int = 0

    project_data = toml_data["project"]
    poetry_data = toml_data["tool"]["poetry"]

    for field in fields:
        if field not in project_data and field not in poetry_data:
            # in neither
            logger.warning(f'"{field}" not found in [project] nor in [tool.poetry]')
        elif field in project_data and field in poetry_data:
            # in both
            logger.info(f'"{field}" found in both [project] and [tool.poetry]')
            if callback(project_data[field]) != callback(poetry_data[field]):
                # values don't equal
                logger.error(
                    f'Values do not match between project.{field}: "{project_data[field]}" '
                    f'and tool.poetry.{field}: "{poetry_data[field]}"'
                )
                number_of_errors += 1
        elif field in project_data:
            # in project only
            logger.warning(f'[project].{field}: "{project_data[field]}", but "{field}" not in [tool.poetry].')
            number_of_errors += 1
        elif field in poetry_data:
            # in tool.poetry only
            logger.warning(f'[tool.poetry].{field}: "{poetry_data[field]}", but "{field}" not in [project].')
            number_of_errors += 1
    return number_of_errors


def check_asymmetric_fields(callback: Callable[[Any], str | set[str]], field_dict: dict, toml_data: dict) -> int:
    """project uses: optional-dependencies.{key} while poetry uses: group.{key}.dependencies
    returns the number of problems detected"""

    number_of_errors: int = 0

    # project_data and poetry_data neet to point to the final field's value
    # Example: for field_dict = field_dict = {'poetry': ['group', 'dev', 'dependencies']}
    # poetry_data will end up pointing to toml_data['tool.poetry.group.dev.dependencies']
    project_data = toml_data["project"]
    poetry_data = toml_data["tool"]["poetry"]

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
        logger.debug(f"[poetry] {poetry_name}:\n{pformat(sorted(package_dependency_field(poetry_data)))}")
        number_of_errors += 1
    return number_of_errors


def check_python_version(toml_data: dict) -> int:
    """There is a special case where the required python version is in different locations:
    project.requires-python and tool.poetry.dependencies.python.
    Also project.requires-python requires a single predicate like ">=3.11" with no upper bound, i.e.
    ">=3.11, <4.0" is invalid.
    """
    number_of_errors: int = 0

    project_data = toml_data["project"]
    poetry_data = toml_data["tool"]["poetry"]

    if "requires-python" in project_data and "python" in poetry_data["dependencies"]:
        # python is specified in both places, so verify their versions are the same
        project_python_version = convert_poetry_to_pep508(project_data["requires-python"])
        poetry_python_version = convert_poetry_to_pep508(poetry_data["dependencies"]["python"], max_bounds=False)
        if project_python_version != poetry_python_version:
            logger.error(
                f"project.requires-python ({project_python_version}) "
                f"does not match tool.poetry.dependencies.python ({poetry_python_version})"
            )
            number_of_errors += 1
    elif "requires-python" in project_data:
        project_python_version = project_data["requires-python"]
        logger.error(
            f"project.requires-python is {project_python_version} but tool.poetry.dependencies.python is missing."
        )
        number_of_errors += 1
    elif "python" in poetry_data["dependencies"]:
        poetry_python_version = convert_poetry_to_pep508(poetry_data["dependencies"]["python"])
        logger.error(
            f"tool.poetry.dependencies.python is {poetry_python_version} but project.requires-python is missing."
        )
        number_of_errors += 1
    else:
        logger.warning("project.requires and tool.poetry.dependencies.python are missing.")
    return number_of_errors


def check_pyproject_toml(toml_data: dict) -> int:
    """check fields that should be identical between [project] and [tool.poetry]
    returns False if there are problems detected"""

    number_of_errors: int = 0

    # group field names by the TOML type of their values

    string_field_names = ["name", "description", "readme", "version", "scripts", "urls"]
    set_field_names = ["keywords", "classifiers"]
    author_field_names = ["authors", "maintainers"]
    dependency_field_names = ["dependencies"]
    optional_dependency_keys = set(toml_data["tool"]["poetry"]["group"]) | set(
        toml_data["project"]["optional-dependencies"]
    )

    # gather all the field names we check, so we can later find the unchecked field names
    checked_field_names = (
        string_field_names
        + set_field_names
        + author_field_names
        + dependency_field_names
        + ["optional-dependencies", "group"]
    )

    # check the field values when the field names are the same in project and tool.poetry tables
    number_of_errors += check_fields(string_field, string_field_names, toml_data)
    number_of_errors += check_fields(set_field, set_field_names, toml_data)
    number_of_errors += check_fields(author_field, author_field_names, toml_data)
    number_of_errors += check_python_version(toml_data)
    n = check_fields(package_dependency_field, dependency_field_names, toml_data)
    if n > 0:
        number_of_errors += n
        pep508_dependencies = package_dependency_field(toml_data["project"]["dependencies"])
        logger.debug("project dependency value(s):\n" + pformat(sorted(pep508_dependencies)).replace("'", '"'))
        pep508_dependencies = package_dependency_field(toml_data["tool"]["poetry"]["dependencies"])
        logger.debug(
            "poetry dependency value(s) formated as pep508:\n" + pformat(sorted(pep508_dependencies)).replace("'", '"')
        )

    # check the field values when the field names differ between project and tool.poetry tables
    for key in optional_dependency_keys:
        field_dict = {"project": ["optional-dependencies", key], "poetry": ["group", key, "dependencies"]}
        number_of_errors += check_asymmetric_fields(package_dependency_field, field_dict, toml_data)

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
    return number_of_errors


def validate_pyproject_toml_file(project_filename: Path) -> int:
    """read the pyproject.toml file then cross validate the [project] and [tool.poetry] sections."""
    try:
        with open(project_filename, "r", encoding="utf-8") as f:
            toml_data = tomllib.loads(f.read())
    except FileNotFoundError:
        logger.error(f'"{project_filename}" is not a file.')
        return 1  # one error
    except IsADirectoryError:
        logger.error(f'"{project_filename}" is a directory, not a pyproject.toml file.')
        return 1  # one error
    except ValueError as err:
        logger.error(f"Unable to parse {project_filename}: {err}")
        return 1  # one error
    number_of_errors = check_pyproject_toml(toml_data)
    logger.info(f"Validate pyproject.toml file: {project_filename} => {number_of_errors} problems detected.")
    return number_of_errors


def main():
    """main function
    If 1 or more arguments are given, they will be passed to `validate_pyproject_toml_file`.
    Else, `validate_pyproject_toml_file` will be called with `$CWD/pyproject.toml`.
    """
    number_of_errors = 0
    args = sys.argv[1:]
    if len(args) == 0:
        args.append(str(Path.cwd() / "pyproject.toml"))
    for arg in args:
        logger.info(f'Checking: "{arg}"')
        number_of_errors += validate_pyproject_toml_file(Path(arg))
    exit(number_of_errors)


if __name__ == "__main__":
    main()
