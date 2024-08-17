# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

"""
This single file script checks that overlapping metadata, between [project] and [tool.poetry] tables, is roughly
 in-sync.

Entry point is the main() function located at the bottom of this file.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from pprint import pformat
from typing import TYPE_CHECKING, Any

from loguru import logger
from packaging.requirements import Requirement

from check_pyproject.poetry_requirement import (
    convert_poetry_specifier_to_pep508,
)

if TYPE_CHECKING:
    from collections.abc import Callable

# valid dependency markers
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


def author_field(value: list[str] | list[dict[str, str]]) -> set[str]:
    """
    Callback to convert author/maintainer fields into project table's format:
    full name <email@example.com>

    returns: set of project table style "user <email>" strings'
    """
    out: set[str] = set()
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
    callback: Callable[[Any], str | set[str] | set[Requirement]], fields: list[str], toml_data: dict[str, Any]
) -> int:
    """
    Check the "project" and "tools.poetry" fields for existence, and equality.
    Returns the number of problems detected
    """
    number_of_problems: int = 0
    project_data: dict[str, Any] = toml_data["project"]
    poetry_data: dict[str, Any] = toml_data["tool"]["poetry"]

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
        elif field in poetry_data:
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
        aa_str = pformat(sorted(aa))
        bb_str = pformat(sorted(bb))
        # format the "a vs b" then replace any "set()" with "{ }" and replace single quotes with double quotes
        return f"project: {aa_str}\nvs\npoetry: {bb_str}".replace("set()", "{ }").replace("'", '"')

    if isinstance(project_data, str) and isinstance(poetry_data, str):
        return f'"{project_data}"\nvs.\n"{poetry_data}"'
    if isinstance(project_data, dict) and isinstance(poetry_data, dict):
        a = {key + "=" + project_data[key] for key in project_data}
        b = {key + "=" + poetry_data[key] for key in poetry_data}
        return set_vs_set(a.difference(b), b.difference(a))
    if isinstance(project_data, list) and isinstance(poetry_data, list):
        a = set(project_data).difference(set(poetry_data))
        b = set(poetry_data).difference(set(project_data))
        return set_vs_set(a, b)
    if isinstance(project_data, set) and isinstance(poetry_data, set):
        a = {str(data) for data in project_data}
        b = {str(data) for data in poetry_data}
        return set_vs_set(a.difference(b), b.difference(a))
    errmsg: str = f"Unexpected type {type(project_data)}"
    raise TypeError(errmsg)


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
            project_python_version = convert_poetry_specifier_to_pep508(project_data["requires-python"])
            poetry_python_version = convert_poetry_specifier_to_pep508(
                poetry_data["dependencies"]["python"], max_bounds=False
            )
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
        poetry_python_version = convert_poetry_specifier_to_pep508(poetry_data["dependencies"]["python"])
        logger.error(
            f"tool.poetry.dependencies.python is {poetry_python_version} but project.requires-python is missing."
        )
        number_of_problems += 1
    else:
        logger.warning("project.requires and tool.poetry.dependencies.python are missing.")
    return number_of_problems


def build_git_url(package_name: str, package_value: dict[str, str], value: str) -> str:
    """
    It is also possible to specify a “git ref” such as branch name, a commit hash or a tag name:
        MyProject @ git+https://git.example.com/MyProject.git@master
        MyProject @ git+https://git.example.com/MyProject.git@v1.0
        MyProject @ git+https://git.example.com/MyProject.git@da39a3ee5e6b4b0d3255bfef95601890afd80709
        MyProject @ git+https://git.example.com/MyProject.git@refs/pull/123/head
    Examples:
        flask = { git = "https://github.com/pallets/flask.git", rev = "38eb5d3b" }
        numpy = { git = "https://github.com/numpy/numpy.git", tag = "v0.13.2" }
        subdir_package = { git = "https://github.com/myorg/mypackage_with_subdirs.git", subdirectory = "subdir" }

    ref: https://pip.pypa.io/en/stable/topics/vcs-support/#git
    """
    value = re.sub(r"^(git@|https://)", r"git+https://", value)
    url = f"{package_name}@ {value}"
    if "rev" in package_value:
        url = f"{url}@{package_value['rev']}"
    elif "tag" in package_value:
        url = f"{url}@{package_value['tag']}"
    if "branch" in package_value:
        url = f"{url}#{package_value['branch']}"
    if "subdirectory" in package_value:
        url = f"{url}/{package_value['subdirectory']}"
    return url


def build_hg_url(package_name: str, package_value: dict[str, str], value: str) -> str:
    """
    It is also possible to specify a revision number, a revision hash, a tag name or a local branch name:
        MyProject @ hg+http://hg.example.com/MyProject@da39a3ee5e6b
        MyProject @ hg+http://hg.example.com/MyProject@2019
        MyProject @ hg+http://hg.example.com/MyProject@v1.0
        MyProject @ hg+http://hg.example.com/MyProject@special_feature
    ref: https://pip.pypa.io/en/stable/topics/vcs-support/#mercurial
    """
    value = re.sub(r"^(hg@|https://)", r"hg+https://", value)
    url = f"{package_name}@ {value}"
    if "rev" in package_value:
        url = f"{url}@{package_value['rev']}"
    elif "branch" in package_value:
        url = f"{url}@{package_value['branch']}"
    elif "tag" in package_value:
        url = f"{url}@{package_value['tag']}"
    if "subdirectory" in package_value:
        # TODO: ??? guessing on this syntax
        url = f"{url}/{package_value['subdirectory']}"
    return url


def build_svn_url(package_name: str, package_value: dict[str, str], value: str) -> str:
    """
    You can also give specific revisions to an SVN URL, like so:
        -e svn+http://svn.example.com/svn/MyProject/trunk@2019#egg=MyProject
        -e svn+http://svn.example.com/svn/MyProject/trunk@{20080101}#egg=MyProject
    ref: https://pip.pypa.io/en/stable/topics/vcs-support/#subversion
    """
    url = re.sub(r"^(svn@|https://)", r"svn+https://", value)
    if "rev" in package_value:
        url = f"{url}@{package_value['rev']}"
    elif "branch" in package_value:
        # TODO: ??? guessing on this syntax
        url = f"{url}@{package_value['branch']}"
    elif "tag" in package_value:
        url = f"{url}@{package_value['tag']}"
    if "subdirectory" in package_value:
        # TODO: ??? guessing on this syntax
        url = f"{url}/{package_value['subdirectory']}"
    return f"{package_name}@ {url}"


def build_bzr_url(package_name: str, package_value: dict[str, str], value: str) -> str:
    """
    Tags or revisions can be installed like so:
        MyProject @ bzr+https://bzr.example.com/MyProject/trunk@2019
        MyProject @ bzr+http://bzr.example.com/MyProject/trunk@v1.0
    ref: https://pip.pypa.io/en/stable/topics/vcs-support/#bazaar
    """
    value = re.sub(r"^(bzr@|https://)", r"bzr+https://", value)
    url = f"{package_name}@ {value}"
    if "rev" in package_value:
        url = f"{url}@{package_value['rev']}"
    elif "branch" in package_value:
        # TODO: ??? guessing on this syntax
        url = f"{url}@{package_value['branch']}"
    elif "tag" in package_value:
        url = f"{url}@{package_value['tag']}"
    if "subdirectory" in package_value:
        # TODO: ??? guessing on this syntax
        url = f"{url}/{package_value['subdirectory']}"
    return url


def build_vcs_url(package_name: str, package_value: dict[str, Any]) -> set[Requirement]:
    """
    Supported VCS: https://hatch.pypa.io/latest/config/dependency/#supported-vcs
    Note order is important because we will check if vcs is in the url (i.e. substring search)
    vcs_schemes = {
        "git": ["git+file", "git+https", "git+ssh", "git+http", "git+git", "git"],
        "hg": ["hg+file", "hg+https", "hg+ssh", "hg+http", "hg+static-http"],
        "svn": ["svn+file", "svn+https", "svn+ssh", "svn+http", "svn+svn", "svn"],
        "bzr": ["bzr+https", "bzr+ssh", "bzr+sftp", "bzr+lp", "bzr+http", "bzr+ftp"],
    }
    VCS URLs: https://pip.pypa.io/en/stable/topics/vcs-support/
    """
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


def add_leftover_markers_to_url(url: str, package_value: dict[str, str], separator: str) -> str:
    """add any leftover markers to url, i.e. markers we have not already explicitly handled."""
    explicitly_handled_markers: list[str] = ["version", "python", "extras", "url", "platform", "source", "optional"]
    markers: set[str] = {mark for mark in package_value if mark not in explicitly_handled_markers}

    if markers:
        _url: str = f"{url}"
        for marker in markers:
            if marker == "markers":
                _url += f"{separator}{package_value[marker]}"
            else:
                _url += f"{separator}{marker}={package_value[marker]}"
        return _url
    return url


def add_markers_to_url(url: str, package_name: str, package_value: dict[str, Any], separator: str = ";") -> str:
    """add markers to the url"""
    if "extras" in package_value:
        value = str(package_value["extras"]).replace("'", "")
        url = f"{package_name}{value} {convert_poetry_specifier_to_pep508(package_value['version'])}"
    if "python" in package_value:
        ver = convert_poetry_specifier_to_pep508(package_value["python"], max_bounds=False, quotes=True)
        url = f"{url};python_version{ver}"
    if "platform" in package_value:
        url = f"{url};sys_platform=='{package_value['platform']}'"

    return add_leftover_markers_to_url(url, package_value, separator)


def build_dict_url(package_name: str, package_value: dict[str, Any]) -> set[Requirement]:
    """create the url for non-version controlled system dependencies"""
    out: set[Requirement] = set()

    if "path" in package_value:
        out.add(Requirement(f"{package_name}@ {package_value['path']}"))
    elif "version" in package_value:
        url = f"{package_name} {convert_poetry_specifier_to_pep508(package_value['version'])}"
        url = add_markers_to_url(url, package_name, package_value)
        out.add(Requirement(url))
    elif "url" in package_value:
        url = f"{package_name}@ {package_value['url']}"
        url = add_markers_to_url(url, package_name, package_value, separator="")
        out.add(Requirement(url))
    else:
        url = f"{package_name}"
        url = add_markers_to_url(url, package_name, package_value, separator="")
        out.add(Requirement(url))

    return out


def dict_to_requirement(package_name: str, package_value: dict[str, Any]) -> set[Requirement]:
    """
    Converts a dictionary to a requirement
    Examples:
        requests3 = { git = "git@github.com:requests/requests.git" }
        pathlib2a = { version = "^2.2", markers = "python_version <= '3.4' or sys_platform == 'win32'" }
        foo1 = [
            {version = "<=1.9", python = ">=3.6,<3.8"},
            {version = "^2.0", python = ">=3.8"}
        ]
    """

    out: set[Requirement] = build_vcs_url(package_name, package_value)

    if not out:
        out = build_dict_url(package_name, package_value)

    if not out:
        logger.warning(f"unable to parse dependency: {package_name} @ {package_value}")
    return out


def list_to_requirement(key: str, values: list[str] | list[dict[str, str]]) -> set[Requirement]:
    """
    Examples:
         foo1 = [
            {version = "<=1.9", python = ">=3.6,<3.8"},
            {version = "^2.0", python = ">=3.8"}
        ]
        foo2 = [
            { platform = "darwin", url = "https://example.com/example-1.0-py3-none-any.whl" },
            { platform = "linux", version = "^1.0" },
        ]
        foo3 = [
            { platform = "darwin", url = "https://example.com/foo-1.0.0-py3-none-macosx_11_0_arm64.whl" },
            { platform = "linux", version = "^1.0", source = "pypi" },
        ]

    """
    out: set[Requirement] = set()
    for value in values:
        if isinstance(value, str):
            out.add(Requirement(f"{key}{convert_poetry_specifier_to_pep508(value)}"))
        if isinstance(value, dict):
            out = out.union(dict_to_requirement(key, value))
    return out


def to_poetry_requirements(
    dependencies: dict[str, str | dict[str, str | list[str]] | list[dict[str, str]]],
) -> set[Requirement]:
    """
    Convert given poetry dependencies to a set of requirements.  Poetry dependencies can be:
    key - str,
    key - list,
    key - dict
    Also poetry specifies the required python as a dependency while project has a requires-python field,
    so ignore any python dependency.
    """
    out: set[Requirement] = set()
    for key, value in dependencies.items():
        if key == "python":
            continue
        if isinstance(value, str):
            out.add(Requirement(f"{key}{convert_poetry_specifier_to_pep508(value)}"))
        elif isinstance(value, list):
            out = out.union(list_to_requirement(key, value))
        elif isinstance(value, dict):
            out = out.union(dict_to_requirement(key, value))
    return out


def check_dependencies(key: str | None, project_dependencies: list[str], poetry_dependencies: dict[str, Any]) -> int:
    """
    Given a list of project dependencies and a dictionary of poetry dependencies, convert each of them
    into a set of requirements.  Then find and report any differences in the sets.
    Return the 1 if any differences are found, 0 otherwise.
    """

    def format_requirement_set(requirements: set[Requirement]) -> str:
        return pformat(sorted([str(r) for r in requirements]))

    number_of_problems: int = 0
    key_str = f'"{key}" ' if key else ""
    project_requirements: set[Requirement] = {Requirement(dep) for dep in project_dependencies}
    poetry_requirements: set[Requirement] = to_poetry_requirements(poetry_dependencies)
    logger.debug(f"{key_str}project_requirements: {format_requirement_set(project_requirements)}")
    logger.debug(f"{key_str}poetry_requirements: {format_requirement_set(poetry_requirements)}")
    differing_requirements = project_requirements.symmetric_difference(poetry_requirements)
    if len(differing_requirements) > 0:
        number_of_problems += 1
        project_to_poetry_diff = project_requirements.difference(poetry_requirements)
        poetry_to_project_diff = poetry_requirements.difference(project_requirements)
        if project_to_poetry_diff or poetry_to_project_diff:
            logger.error(
                f"Dependencies {key_str}Differences:\n"
                f"{format_diff_values(project_to_poetry_diff, poetry_to_project_diff)}"
            )
    return number_of_problems


# noinspection PyBroadException
def check_pyproject_toml(toml_data: dict[str, Any]) -> int:
    """
    Check fields that should be identical between [project] and [tool.poetry]
    Returns then number of problems detected.
    """

    number_of_problems: int = 0

    try:
        poetry_data = toml_data["tool"]["poetry"]
    except KeyError:
        logger.error("pyproject missing tool.poetry section.")
        return 0
    try:
        project_data = toml_data["project"]
    except KeyError:
        logger.error("pyproject missing tool.project section.")
        return 0

    try:
        # group field names by the TOML type of their values
        string_field_names: list[str] = ["name", "description", "readme", "version", "scripts", "urls"]
        set_field_names: list[str] = ["keywords", "classifiers"]
        author_field_names: list[str] = ["authors", "maintainers"]
        dependency_field_names: list[str] = ["dependencies"]
        optional_dependency_keys: set[str] = set(poetry_data["group"]) | set(project_data["optional-dependencies"])

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
    except Exception:
        # This is a catch-all.  We intentionally want to capture any exception here so they
        # are counted as a problem and logged.
        logger.exception("Problem checking pyproject.toml:")
        number_of_problems += 1
    return number_of_problems


def validate_pyproject_toml_file(project_filename: Path) -> int:
    """read the pyproject.toml file then cross validate the [project] and [tool.poetry] sections."""
    number_of_problems: int = 0
    try:
        logger.info(f"Reading pyproject.toml file: {project_filename}")
        with Path(project_filename).open(encoding="utf-8") as f:
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
    logger.info(f"Check pyproject.toml file: {project_filename} => {number_of_problems} problems detected.\n")
    return number_of_problems
