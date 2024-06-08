"""
This single file script checks that overlapping metadata, between [project] and [tool.poetry] tables, is roughly
 in-sync.

Entry point is the main() function located at the bottom of this file.
"""

import re
import tomllib
from pathlib import Path
from pprint import pformat
from typing import Callable, Any
from loguru import logger
from packaging.requirements import Requirement
from check_pyproject.poetry_requirement import (
    convert_poetry_to_pep508,
)

valid_markers_set = {
    "os_name",  # posix, java
    "sys_platform",  # linux, linux2, darwin, java1.8.0_51
    "platform_machine",  # x86_64
    "platform_python_implementation",  # CPython, Jython
    "platform_release",  # 3.14.1-x86_64-linode39, 14.5.0, 1.8.0_51
    "platform_system",  # Linux, Windows, Java
    "platform_version",  # #1 SMP Fri Apr 25 13:07:35 EDT 2014 Java HotSpot(TM) 64-Bit Server VM, ...
    "python_version",  # 3.4, 2.7
    "python_full_version",  # 3.4.0, 3.5.0b1
    "implementation_name",  # cpython
    "implementation_version",  # 3.4.0, 3.5.0b1
}


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


def check_fields(
    callback: Callable[[Any], str | set[str] | set[Requirement]], fields: list, toml_data: dict[str, Any]
) -> int:
    """
    Check the "project" and "tools.poetry" fields for existence, and equality.
    Returns the number of problems detected
    """
    number_of_problems: int = 0
    project_data: dict = toml_data["project"]
    poetry_data: dict = toml_data["tool"]["poetry"]

    for field in fields:
        if field in project_data:
            # in project
            if field in poetry_data:
                # in both
                logger.info(f'"{field}" found in both [project] and [tool.poetry]')
                project_out = callback(project_data[field])
                poetry_out = callback(poetry_data[field])
                if project_out != poetry_out:
                    # values don't equal
                    logger.error(
                        f"Values do not match between project.{field} and tool.poetry.{field}.\n"
                        f"Differences:\n{format_diff_values(project_out, poetry_out)}"
                    )
                    number_of_problems += 1
            else:
                # not in tool.poetry, so in project only
                logger.warning(f'[project].{field}: "{project_data[field]}", but "{field}" not in [tool.poetry].')
                number_of_problems += 1
        else:
            # not in project
            if field in poetry_data:
                # in tool.poetry only
                logger.warning(f'[tool.poetry].{field}: "{poetry_data[field]}", but "{field}" not in [project].')
                number_of_problems += 1
            else:
                # in neither
                logger.warning(f'"{field}" not found in [project] nor in [tool.poetry]')

    return number_of_problems


def format_diff_values(
    project_data: str | list[str] | dict[str, Any] | set[Any], poetry_data: str | list[str] | dict[str, Any] | set[Any]
) -> str:
    """
    Format the differences between project and poetry values, but not dependencies.
    """
    def set_vs_set(aa: set[str], bb: set[str]) -> str:
        aa_str = pformat(sorted(list(aa)))
        bb_str = pformat(sorted(list(bb)))
        # format the "a vs b" then replace any "set()" with "{ }" and replace single quotes with double quotes
        return f"{aa_str}\nvs\n{bb_str}".replace("set()", "{ }").replace("'", '"')

    if isinstance(project_data, str):
        return f'"{project_data}"\nvs.\n"{poetry_data}"'
    if isinstance(project_data, dict):
        a = {key + "=" + project_data[key] for key in project_data}
        b = {key + "=" + poetry_data[key] for key in poetry_data}
        return set_vs_set(a.difference(b), b.difference(a))
    if isinstance(project_data, list):
        a = set(project_data).difference(set(poetry_data))
        b = set(poetry_data).difference(set(project_data))
        return set_vs_set(a, b)
    if isinstance(project_data, set):
        a = {str(data) for data in project_data}
        b = {str(data) for data in poetry_data}
        return set_vs_set(a.difference(b), b.difference(a))
    raise TypeError(f"Unexpected type {type(project_data)}")


def check_python_version(toml_data: dict[str, Any]) -> int:
    """
    There is a special case where the required python version is in different locations:
    project.requires-python and tool.poetry.dependencies.python.
    Also project.requires-python requires a single predicate like ">=3.11" with no upper bound, i.e.
    ">=3.11, <4.0" is invalid.

    Returns then number of problems detected.
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


def to_project_requirements(dependency_list: list[str]) -> set[Requirement]:
    return {Requirement(dep) for dep in dependency_list}


def list_to_requirement(key: str, value: list[str | dict[str, str]]) -> Requirement | None:
    return None


def build_git_url(package_name: str, package_value: dict[str, str], value: str) -> str:
    value = re.sub(r"^(git@|https://)", r"git+https://", value)
    url = f"{package_name}@ {value}"
    if "rev" in package_value:
        url = f"{url}@{package_value['rev']}"
    elif "branch" in package_value:
        url = f"{url}#{package_value['branch']}"
    elif "tag" in package_value:
        url = f"{url}@{package_value['tag']}"
    return url


def build_hg_url(package_name: str, package_value: dict[str, str], value: str) -> str:
    url = f"{package_name}@ {value}"
    # TODO implement
    return url


def build_svn_url(package_name: str, package_value: dict[str, str], value: str) -> str:
    url = f"{package_name}@ {value}"
    # TODO implement
    return url


def build_bzr_url(package_name: str, package_value: dict[str, str], value: str) -> str:
    url = f"{package_name}@ {value}"
    # TODO implement
    return url


def build_vcs_url(package_name: str, package_value: dict[str, str]) -> set[Requirement]:
    # Supported VCS: https://hatch.pypa.io/latest/config/dependency/#supported-vcs
    # Note order is important because we will check if vcs is in the url (i.e. substring search)
    # vcs_schemes = {
    #     "git": ["git+file", "git+https", "git+ssh", "git+http", "git+git", "git"],
    #     "hg": ["hg+file", "hg+https", "hg+ssh", "hg+http", "hg+static-http"],
    #     "svn": ["svn+file", "svn+https", "svn+ssh", "svn+http", "svn+svn", "svn"],
    #     "bzr": ["bzr+https", "bzr+ssh", "bzr+sftp", "bzr+lp", "bzr+http", "bzr+ftp"],
    # }
    vcs_builder = {
        "git": build_git_url,
        "hg": build_hg_url,
        "svn": build_svn_url,
        "bzr": build_bzr_url,
    }
    out: set[Requirement] = set()
    for vcs in vcs_builder:
        if vcs in package_value:
            value = package_value[vcs]
            url = vcs_builder[vcs](package_name, package_value, value)
            out.add(Requirement(url))
            break
    return out


def add_leftover_markers_to_url(url: str, package_name: str, package_value: dict[str, str]) -> str:
    markers = set(
        [
            mark + str(package_value[mark])
            for mark in package_value
            if mark not in ["version", "python", "extras"]
        ]
    )
    extra_markers = markers.intersection(valid_markers_set)
    if extra_markers:
        url = f"{url}; {'; '.join(extra_markers)}"
    return url


def add_markers_to_url(url: str, package_name: str, package_value: dict[str, str]) -> str:
    if "extras" in package_value:
        value = str(package_value["extras"]).replace("'", "")
        url = f"{package_name}{value} {convert_poetry_to_pep508(package_value['version'])}"
    if "python" in package_value:
        ver = convert_poetry_to_pep508(package_value["python"], max_bounds=False, quotes=True)
        url = f"{url};python_version{ver}"

    add_leftover_markers_to_url(url, package_name, package_value)
    return url


def build_dict_url(package_name: str, package_value: dict[str, str]) -> set[Requirement]:
    out: set[Requirement] = set()

    if "path" in package_value:
        out.add(Requirement(f"{package_name}@ {package_value['path']}"))
    elif "source" in package_value:
        out.add(Requirement(f"{package_name}@ {package_value['source']}"))
    elif "version" in package_value:
        url = f"{package_name} {convert_poetry_to_pep508(package_value['version'])}"
        url = add_markers_to_url(url, package_name, package_value)
        out.add(Requirement(url))
    return out


def dict_to_requirement(package_name: str, package_value: dict[str, str]) -> set[Requirement]:
    """
    flask = { git = "https://github.com/pallets/flask.git", rev = "38eb5d3b" }
    numpy = { git = "https://github.com/numpy/numpy.git", tag = "v0.13.2" }
    subdir_package = { git = "https://github.com/myorg/mypackage_with_subdirs.git", subdirectory = "subdir" }
    requests3 = { git = "git@github.com:requests/requests.git" }
    """

    out: set[Requirement] = build_vcs_url(package_name, package_value)

    if not out:
        out = build_dict_url(package_name, package_value)

    if not out:
        logger.warning(f"unable to parse dependency: {package_name} @ {package_value}")
    return out


def to_poetry_requirements(dependencies: dict[str, str | dict[str, str] | list[dict[str, str]]]) -> set[Requirement]:
    out: set[Requirement] = set()
    for key, value in dependencies.items():
        if key == "python":
            continue
        if isinstance(value, str):
            out.add(Requirement(f"{key}{convert_poetry_to_pep508(value)}"))
        elif isinstance(value, list):
            req_list = list_to_requirement(key, value)
            if req_list:
                out.add(req_list)
        elif isinstance(value, dict):
            out = out.union(dict_to_requirement(key, value))
    return out


def format_requirement_set(requirements: set[Requirement]) -> str:
    return pformat(sorted([str(r) for r in requirements]))


def check_dependencies(key: str | None, project_dependencies: list[str], poetry_dependencies: dict[str, Any]) -> int:
    number_of_problems: int = 0
    project_requirements: set[Requirement] = to_project_requirements(project_dependencies)
    poetry_requirements: set[Requirement] = to_poetry_requirements(poetry_dependencies)
    logger.debug(f"project_requirements: {format_requirement_set(project_requirements)}")
    logger.debug(f"poetry_requirements: {format_requirement_set(poetry_requirements)}")
    differing_requirements = project_requirements.symmetric_difference(poetry_requirements)
    if len(differing_requirements) > 0:
        number_of_problems += 1
        project_to_poetry_diff = project_requirements.difference(poetry_requirements)
        poetry_to_project_diff = poetry_requirements.difference(project_requirements)
        key_str = f'"{key}" ' if key else ""
        if project_to_poetry_diff:
            logger.info(f"{key_str}requirements only in project:\n{format_requirement_set(project_to_poetry_diff)}")
        if poetry_to_project_diff:
            logger.info(f"{key_str}requirements only in poetry:\n{format_requirement_set(poetry_to_project_diff)}")
    return number_of_problems


def check_pyproject_toml(toml_data: dict[str, Any]) -> int:
    """
    Check fields that should be identical between [project] and [tool.poetry]
    Returns then number of problems detected.
    """

    number_of_problems: int = 0

    try:
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
        number_of_problems += check_dependencies(
            None, toml_data["project"]["dependencies"], toml_data["tool"]["poetry"]["dependencies"]
        )

        # check the field values when the field names differ between project and tool.poetry tables
        key: str
        for key in optional_dependency_keys:
            number_of_problems += check_dependencies(
                key,
                toml_data["project"]["optional-dependencies"][key],
                toml_data["tool"]["poetry"]["group"][key]["dependencies"],
            )

        # warn about fields not checked
        logger.warning(
            f"Fields not checked in [project]:  {sorted(toml_data['project'].keys() - checked_field_names)}"
        )
        logger.warning(
            f"Fields not checked in [tool.poetry]:  {sorted(toml_data['tool']['poetry'].keys() - checked_field_names)}"
        )
        logger.info(
            "Note that the license tables have completely different formats between\n"
            "[project] (takes either a file or a text attribute of the actual license and "
            "[tool.poetry] (takes the name of the license), so both must be manually set."
        )
    except Exception:  # NOQA - Intentionally want to capture any exception here
        logger.exception("Problem checking pyproject.toml:")
        number_of_problems += 1
    return number_of_problems


def validate_pyproject_toml_file(project_filename: Path) -> int:
    """read the pyproject.toml file then cross validate the [project] and [tool.poetry] sections."""
    number_of_problems: int = 0
    try:
        logger.info(f"Reading pyproject.toml file: {project_filename}")
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
