# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from pprint import pformat
from typing import Any

import pytest
from loguru import logger
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet

from check_pyproject.check_pyproject_toml import (
    add_leftover_markers_to_url,
    check_fields,
    format_diff_values,
    string_field,
    to_poetry_requirements,
    validate_pyproject_toml_file,
)
from check_pyproject.clibones.logger_control import LOGURU_SHORT_FORMAT
from check_pyproject.poetry_requirement import caret_requirement_to_pep508, convert_poetry_specifier_to_pep508
from check_pyproject.version_utils import VersionUtils

logger.remove(None)
logger.add(sys.stderr, level="DEBUG", format=LOGURU_SHORT_FORMAT)


def test_all_good_pyproject() -> None:
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "good_pyproject.toml")
    assert number_of_problems == 0


def test_optional_deps_pyproject() -> None:
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "optional_deps_pyproject.toml")
    assert number_of_problems == 0


def test_all_bad_pyproject() -> None:
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "bad_pyproject.toml")
    assert number_of_problems == 14


def test_bad_python_pyproject() -> None:
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "bad_python_pyproject_1.toml")
    assert number_of_problems == 1


def test_bad_python_pyproject_2() -> None:
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "bad_python_pyproject_2.toml")
    assert number_of_problems == 1


def test_bad_python_pyproject_3() -> None:
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "bad_python_pyproject_3.toml")
    assert number_of_problems == 0


def test_mixed_pyproject() -> None:
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "mixed_pyproject.toml")
    assert number_of_problems == 6


def test_nonexistent_file() -> None:
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "xyzzy")  # :-)
    assert number_of_problems == 1


def test_invalid_pyproject_file() -> None:
    # ASSUMES README.md is in the parent directory of the directory of this test
    # i.e.: ./this_test.py and ../README.md
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent.parent / "README.md")
    assert number_of_problems == 1


def test_directory() -> None:
    # ASSUMES pyproject.toml is in the parent directory of the directory of this test
    # i.e.: ./this_test.py so ../pyproject.toml
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent.parent)
    assert number_of_problems == 1


def test_missing_field() -> None:
    with (Path(__file__).parent / "good_pyproject.toml").open(encoding="utf-8") as f:
        toml_data: dict[str, Any] = tomllib.loads(f.read())
    assert check_fields(string_field, ["bogus"], toml_data) == 0


def test_convert_poetry_to_pep508() -> None:
    # ref: https://python-poetry.org/docs/dependency-specification/
    # Caret requirements
    assert SpecifierSet(">=1.2.3, <2.0.0") == SpecifierSet(convert_poetry_specifier_to_pep508("^1.2.3")), "^1.2.3"

    assert SpecifierSet(">=1.2.0, <2.0.0") == SpecifierSet(convert_poetry_specifier_to_pep508("^1.2")), "^1.2"
    assert SpecifierSet(">=1.0.0, <2.0.0") == SpecifierSet(convert_poetry_specifier_to_pep508("^1")), "^1"
    assert SpecifierSet(">=0.2.3, <0.3.0") == SpecifierSet(convert_poetry_specifier_to_pep508("^0.2.3")), "^0.2.3"
    assert SpecifierSet(">=0.0.3, <0.0.4") == SpecifierSet(convert_poetry_specifier_to_pep508("^0.0.3")), "^0.0.3"
    assert SpecifierSet(">=0.0.0, <0.1.0") == SpecifierSet(convert_poetry_specifier_to_pep508("^0.0")), "^0.0"
    assert SpecifierSet(">=0.0.0, <1.0.0") == SpecifierSet(convert_poetry_specifier_to_pep508("^0")), "^0"

    # Tilde requirements
    assert SpecifierSet(">=1.2.3, <1.3.0") == SpecifierSet(convert_poetry_specifier_to_pep508("~1.2.3")), "~1.2.3"
    assert SpecifierSet(">=1.2.0, <1.3.0") == SpecifierSet(convert_poetry_specifier_to_pep508("~1.2")), "~1.2"
    assert SpecifierSet(">=1.0.0, <2.0.0") == SpecifierSet(convert_poetry_specifier_to_pep508("~1")), "~1"

    # Wildcard requirements
    assert SpecifierSet(">=0.0.0") == SpecifierSet(convert_poetry_specifier_to_pep508("*")), "*"
    assert SpecifierSet(">=1.0.0, <2.0.0") == SpecifierSet(convert_poetry_specifier_to_pep508("1.*")), "1.*"
    assert SpecifierSet(">=1.2.0, <1.3.0") == SpecifierSet(convert_poetry_specifier_to_pep508("1.2.*")), "1.2.*"

    # Inequality requirements
    assert SpecifierSet(">=1.2.0") == SpecifierSet(convert_poetry_specifier_to_pep508(">= 1.2.0")), ">= 1.2.0"
    assert SpecifierSet(">1.0.0") == SpecifierSet(convert_poetry_specifier_to_pep508("> 1")), "> 1"
    assert SpecifierSet("<2.0.0") == SpecifierSet(convert_poetry_specifier_to_pep508("< 2")), "< 2"
    assert SpecifierSet("!=1.2.4") == SpecifierSet(convert_poetry_specifier_to_pep508("!= 1.2.4")), "!= 1.2.4"

    # Multiple requirements
    assert SpecifierSet(">=1.2.0, !=1.2.4") == SpecifierSet(
        convert_poetry_specifier_to_pep508(">= 1.2.0, != 1.2.4")
    ), ">= 1.2.0, != 1.2.4"
    assert SpecifierSet(">=1.2.0, <1.5.0") == SpecifierSet(
        convert_poetry_specifier_to_pep508(">= 1.2, < 1.5")
    ), ">= 1.2, < 1.5"

    # Exact requirements
    assert SpecifierSet("==1.2.3") == SpecifierSet(convert_poetry_specifier_to_pep508("==1.2.3")), "==1.2.3"
    assert SpecifierSet("==1.2.0") == SpecifierSet(convert_poetry_specifier_to_pep508("==1.2")), "==1.2"
    assert SpecifierSet("==1.0.0") == SpecifierSet(convert_poetry_specifier_to_pep508("==1")), "==1"

    # note, packaging module does not allow bare version numbers, ex: "1.2.3"


def test_fill_version_to_three_parts() -> None:
    assert VersionUtils.fill_version_to_three_parts("") == "0.0.0"
    assert VersionUtils.fill_version_to_three_parts("0") == "0.0.0"
    assert VersionUtils.fill_version_to_three_parts("0.0") == "0.0.0"
    assert VersionUtils.fill_version_to_three_parts("0.0.0") == "0.0.0"


def test_dependency_extras() -> None:
    expected: str = str(Requirement("unicorn[all,gevent]>=20.1.0"))
    results: set[Requirement] = to_poetry_requirements({"unicorn": {"extras": ["gevent", "all"], "version": ">=20.1"}})
    assert len(results) == 1, "one pep508 requirement generated"
    assert expected == str(results.pop()), "unicorn[gevent]>=20.1.0"


def test_dependency_two_extras() -> None:
    expected: str = str(Requirement("unicorn[gevent,mysql]>=20.1.1"))
    results: set[Requirement] = to_poetry_requirements(
        {"unicorn": {"extras": ["gevent", "mysql"], "version": ">=20.1.1"}}
    )
    assert len(results) == 1, "one pep508 requirement generated"
    assert expected == str(results.pop()), "unicorn[gevent]>=20.1.1"


def test_optional_dependency() -> None:
    expected: str = str(Requirement("unicorn>=20.1.0"))
    results: set[Requirement] = to_poetry_requirements({"unicorn": {"optional": "true", "version": ">=20.1"}})
    assert len(results) == 1, "one pep508 requirement generated"
    assert expected == str(results.pop()), "unicorn>=20.1.0, optional=true"


def test_git_dependency() -> None:
    expected: str = str(Requirement("check-pyproject@ git+https://github.com:royw/check_pyproject.git"))
    results: set[Requirement] = to_poetry_requirements(
        {"check-pyproject": {"git": "git@github.com:royw/check_pyproject.git"}}
    )
    assert len(results) == 1, "one pep508 requirement generated"
    assert expected == str(results.pop()), "check-pyproject@git+https://github.com:royw/check_pyproject.git"


def test_caret_requirement_to_pep508() -> None:
    assert str(SpecifierSet(">=1.2.3")) == caret_requirement_to_pep508(
        "^1.2.3"[1:], max_bounds=False
    ), "^1.2.3 max_bounds=False"
    assert str(SpecifierSet(">=1.2.3,<2.0.0")) == caret_requirement_to_pep508(
        "^1.2.3"[1:], max_bounds=True
    ), "^1.2.3 max_bounds=True"


def test_hg_vcs() -> None:
    dependencies = tomllib.loads("""
    foo1 = {hg = "https://foohub.com/foo1/foo1.hg"}
    foo2 = {hg = "https://foohub.com/foo2/foo2.hg", branch = "next"}
    foo3 = {hg = "https://foohub.com/foo3/foo3.hg", rev = "38eb5d3b"}
    foo4 = {hg = "https://foohub.com/foo4/foo4.hg", tag = "v0.13.2"}
    foo5 = {hg = "https://foohub.com/foo5/foo5.hg", subdirectory = "subdir"}
    """)
    target_requirements = {
        Requirement("foo1@ hg+https://foohub.com/foo1/foo1.hg"),
        Requirement("foo2@ hg+https://foohub.com/foo2/foo2.hg@next"),
        Requirement("foo3@ hg+https://foohub.com/foo3/foo3.hg@38eb5d3b"),
        Requirement("foo4@ hg+https://foohub.com/foo4/foo4.hg@v0.13.2"),
        Requirement("foo5@ hg+https://foohub.com/foo5/foo5.hg/subdir"),
    }
    requirements = to_poetry_requirements(dependencies)
    diff = requirements.symmetric_difference(target_requirements)
    assert len(diff) == 0, f"Hg Diff: {pformat(diff)}"


def test_svn_vcs() -> None:
    dependencies = tomllib.loads("""
    foo1 = {svn = "https://foohub.com/foo1/foo1.svn"}
    foo2 = {svn = "https://foohub.com/foo2/foo2.svn", branch = "next"}
    foo3 = {svn = "https://foohub.com/foo3/foo3.svn", rev = "38eb5d3b"}
    foo4 = {svn = "https://foohub.com/foo4/foo4.svn", tag = "v0.13.2"}
    foo5 = {svn = "https://foohub.com/foo5/foo5.svn", subdirectory = "subdir"}
    """)
    target_requirements = {
        Requirement("foo1@ svn+https://foohub.com/foo1/foo1.svn"),
        Requirement("foo2@ svn+https://foohub.com/foo2/foo2.svn@next"),
        Requirement("foo3@ svn+https://foohub.com/foo3/foo3.svn@38eb5d3b"),
        Requirement("foo4@ svn+https://foohub.com/foo4/foo4.svn@v0.13.2"),
        Requirement("foo5@ svn+https://foohub.com/foo5/foo5.svn/subdir"),
    }
    requirements = to_poetry_requirements(dependencies)
    diff = requirements.symmetric_difference(target_requirements)
    assert len(diff) == 0, f"svn Diff: {pformat(diff)}"


def test_bzr_vcs() -> None:
    dependencies = tomllib.loads("""
    foo1 = {bzr = "https://foohub.com/foo1/foo1.bzr"}
    foo2 = {bzr = "https://foohub.com/foo2/foo2.bzr", branch = "next"}
    foo3 = {bzr = "https://foohub.com/foo3/foo3.bzr", rev = "38eb5d3b"}
    foo4 = {bzr = "https://foohub.com/foo4/foo4.bzr", tag = "v0.13.2"}
    foo5 = {bzr = "https://foohub.com/foo5/foo5.bzr", subdirectory = "subdir"}
    """)
    target_requirements = {
        Requirement("foo1@ bzr+https://foohub.com/foo1/foo1.bzr"),
        Requirement("foo2@ bzr+https://foohub.com/foo2/foo2.bzr@next"),
        Requirement("foo3@ bzr+https://foohub.com/foo3/foo3.bzr@38eb5d3b"),
        Requirement("foo4@ bzr+https://foohub.com/foo4/foo4.bzr@v0.13.2"),
        Requirement("foo5@ bzr+https://foohub.com/foo5/foo5.bzr/subdir"),
    }
    requirements = to_poetry_requirements(dependencies)
    diff = requirements.symmetric_difference(target_requirements)
    assert len(diff) == 0, f"bzr Diff: {pformat(diff)}"


def test_format_diff_values_set() -> None:
    project_data = {Requirement(f"1.2.{n}") for n in range(10)}
    poetry_data = {Requirement(f"1.2.{2 * n}") for n in range(10)}
    out_str = format_diff_values(project_data=project_data, poetry_data=poetry_data)
    assert out_str == (
        'project: ["1.2.1", "1.2.3", "1.2.5", "1.2.7", "1.2.9"]\n'
        "vs\n"
        'poetry: ["1.2.10", "1.2.12", "1.2.14", "1.2.16", "1.2.18"]'
    )


def test_format_diff_values_list() -> None:
    project_data = [f"1.2.{n}" for n in range(10)]
    poetry_data = [f"1.2.{2 * n}" for n in range(10)]
    out_str = format_diff_values(project_data=project_data, poetry_data=poetry_data)
    assert out_str == (
        'project: ["1.2.1", "1.2.3", "1.2.5", "1.2.7", "1.2.9"]\n'
        "vs\n"
        'poetry: ["1.2.10", "1.2.12", "1.2.14", "1.2.16", "1.2.18"]'
    )


def test_format_diff_values_tuple() -> None:
    """tuple is not supported, so this is testing error handling."""
    project_data = tuple([f"1.2.{n}" for n in range(10)])
    poetry_data = tuple([f"1.2.{2 * n}" for n in range(10)])
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        format_diff_values(project_data=project_data, poetry_data=poetry_data)  # type: ignore[arg-type]


def test_add_leftover_markers_to_url() -> None:
    data = add_leftover_markers_to_url(
        url="https://example.com", package_value={"foo": "1", "bar": "2"}, separator=";"
    )
    assert data in ["https://example.com;foo=1;bar=2", "https://example.com;bar=2;foo=1"]
