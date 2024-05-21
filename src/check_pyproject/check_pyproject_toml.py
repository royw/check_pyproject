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
import tomllib
from pathlib import Path
from pprint import pformat

from loguru import logger
from versio.version import Version
from versio.version_scheme import Pep440VersionScheme


def max_version(version_str: str) -> str:
    """bump the version number to the upper bound of the version.
    Examples:
        "1.2.4" will be bumped to "2.0.0"
        "0.1.2" will be bumped to "0.2.0"
        "0.0.7" will be bumped to "0.0.8"
    """
    ver: Version = Version(version_str, scheme=Pep440VersionScheme)
    index: int = 0
    for part in str(ver).split("."):
        if int(part) > 0:
            break
        index += 1
    ver.bump("release", index)
    return str(ver)


def convert_poetry_to_pep508(value: str, max_bounds=True) -> str:
    """convert poetry dependency specifiers(^v.v, ~v.v, v.*) to pep508 format
    returns a string containing comma separated pep508 specifiers
    """
    # TODO add support for all poetry dependency specifiers
    out: list[str] = []
    for part in re.split(r"[,\s]", value):
        # ^a.b.c
        if part.startswith("^"):
            if max_bounds:
                out.append(f">={part[1:]}, <{max_version(part[1:])}")
            else:
                out.append(f">={part[1:]}")
        if part.startswith("~"):
            out.append(f"~={part[1:]}")
        if "*" in part:
            pass
    return ", ".join(out)


def package_dependency_field(value: list[str] | dict[str, str]) -> set[str]:
    """callback to convert a package dependency specifiers into a set of package dependency fields.
    list[str] values should be from the project table and already in pep508 format.
    dict[str, str] should be from the tool.poetry table and need conversion to pep508 format.

    There is a special case where the required python version is in different locations:
    project.requires-python and tool.poetry.dependencies.python.  So for poetry dependencies
    we skip "python" and handle the special case elsewhere.

    returns set of pep508 dependency fields.
    """
    out: set = set()
    if isinstance(value, list):
        for v in value:
            if isinstance(v, str):
                # should be pep508 dependency metadata
                out.add(v)

    if isinstance(value, dict):
        # should be poetry dependency metadata
        for key, v in value.items():
            if key == "python":
                continue
            if isinstance(v, str):
                out.add(f"{key}{convert_poetry_to_pep508(v)}")
            if isinstance(v, dict):
                if "extras" in v and "version" in v:
                    out.add(f"{key}{v['extras']}{convert_poetry_to_pep508(v['version'])}")
    return out


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


def check_fields(callback, fields: list, toml_data: dict) -> int:
    """check the fields for existence, and equality.
    returns the number of problems detected"""
    number_of_errors: int = 0

    for field in fields:
        if field not in toml_data["project"] and field not in toml_data["tool"]["poetry"]:
            # in neither
            logger.warning(f'"{field}" not found in [project] nor in [tool.poetry]')
        elif field in toml_data["project"] and field in toml_data["tool"]["poetry"]:
            # in both
            logger.info(f'"{field}" found in both [project] and [tool.poetry]')
            if callback(toml_data["project"][field]) != callback(toml_data["tool"]["poetry"][field]):
                # values don't equal
                logger.error(
                    f"Values do not match between project.{field}: \"{toml_data['project'][field]}\" "
                    f"and tool.poetry.{field}: \"{toml_data['tool']['poetry'][field]}\""
                )
                number_of_errors += 1
        elif field in toml_data["project"]:
            # in project only
            logger.warning(
                f"[project].{field}: \"{toml_data['project'][field]}\", " f" but \"{field}\" not in [tool.poetry]."
            )
            number_of_errors += 1
        elif field in toml_data["tool"]["poetry"]:
            # in tool.poetry only
            logger.warning(
                f"[tool.poetry].{field}: \"{toml_data['tool']['poetry'][field]}\", "
                f" but \"{field}\" not in [project]."
            )
            number_of_errors += 1
    return number_of_errors


def check_asymmetric_fields(callback, field_dict: dict, toml_data: dict) -> int:
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
        logger.error(f"[project.{project_name}] " f"does not match poetry.{poetry_name}")
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
    if "requires-python" in toml_data["project"] and "python" in toml_data["tool"]["poetry"]["dependencies"]:
        # python is specified in both places, so verify their versions are the same
        project_python_version = toml_data["project"]["requires-python"]
        poetry_python_version = convert_poetry_to_pep508(
            toml_data["tool"]["poetry"]["dependencies"]["python"], max_bounds=False
        )
        if project_python_version != poetry_python_version:
            logger.error(
                f"project.requires-python ({project_python_version}) "
                f"does not match tool.poetry.dependencies.python ({poetry_python_version})"
            )
            number_of_errors += 1
    elif "requires-python" in toml_data["project"]:
        project_python_version = toml_data["project"]["requires-python"]
        logger.error(
            f"project.requires-python is {project_python_version} " f"but tool.poetry.dependencies.python is missing."
        )
        number_of_errors += 1
    elif "python" in toml_data["tool"]["poetry"]["dependencies"]:
        poetry_python_version = convert_poetry_to_pep508(toml_data["tool"]["poetry"]["dependencies"]["python"])
        logger.error(
            f"tool.poetry.dependencies.python is {poetry_python_version} " f"but project.requires-python is missing."
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

    # gather all the field names we check so we can later find the unchecked field names
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
    logger.warning(
        f"Fields not checked in [project]: " f" {sorted(toml_data['project'].keys() - checked_field_names)}"
    )
    logger.warning(
        f"Fields not checked in [tool.poetry]: " f" {sorted(toml_data['tool']['poetry'].keys() - checked_field_names)}"
    )
    logger.info(
        "Note that the license tables have completely different formats between\n"
        "[project] (takes either a file or a text attribute of the actual license and "
        "[tool.poetry] (takes the name of the license), so both must be manually set."
    )
    return number_of_errors


def validate_pyproject_toml_file(project_filename: Path) -> int:
    """read the good_pyproject.toml file then cross validate the [project] and [tool.poetry] sections."""
    with open(project_filename, "r", encoding="utf-8") as f:
        toml_data = tomllib.loads(f.read())

    number_of_errors = check_pyproject_toml(toml_data)
    logger.info(f"Validate good_pyproject.toml file: {project_filename} => {number_of_errors} problems detected.")
    return number_of_errors


def main():
    exit(validate_pyproject_toml_file(Path.cwd() / "pyproject.toml"))


if __name__ == "__main__":
    main()
