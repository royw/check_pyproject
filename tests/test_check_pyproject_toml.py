import sys
from pathlib import Path
from typing import Any

import tomllib
from loguru import logger
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet

from check_pyproject.check_pyproject_toml import (
    check_fields,
    convert_poetry_specifier_to_pep508,
    string_field,
    to_poetry_requirements,
    validate_pyproject_toml_file,
)
from check_pyproject.clibones.logger_control import LOGURU_SHORT_FORMAT
from check_pyproject.poetry_requirement import caret_requirement_to_pep508
from check_pyproject.version_utils import VersionUtils

logger.remove(None)
logger.add(sys.stderr, level="DEBUG", format=LOGURU_SHORT_FORMAT)


def test_all_good_pyproject():
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "good_pyproject.toml")
    assert number_of_problems == 0


def test_optional_deps_pyproject():
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "optional_deps_pyproject.toml")
    assert number_of_problems == 0


def test_all_bad_pyproject():
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "bad_pyproject.toml")
    assert number_of_problems == 14


def test_bad_python_pyproject():
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "bad_python_pyproject_1.toml")
    assert number_of_problems == 1


def test_bad_python_pyproject_2():
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "bad_python_pyproject_2.toml")
    assert number_of_problems == 1


def test_bad_python_pyproject_3():
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "bad_python_pyproject_3.toml")
    assert number_of_problems == 0


def test_mixed_pyproject():
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "mixed_pyproject.toml")
    assert number_of_problems == 6


def test_nonexistent_file():
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "xyzzy")  # :-)
    assert number_of_problems == 1


def test_invalid_pyproject_file():
    # ASSUMES README.md is in the parent directory of the directory of this test
    # i.e.: ./this_test.py and ../README.md
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent.parent / "README.md")
    assert number_of_problems == 1


def test_directory():
    # ASSUMES pyproject.toml is in the parent directory of the directory of this test
    # i.e.: ./this_test.py so ../pyproject.toml
    number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent.parent)
    assert number_of_problems == 1


def test_missing_field():
    with open(Path(__file__).parent / "good_pyproject.toml", encoding="utf-8") as f:
        toml_data: dict[str, Any] = tomllib.loads(f.read())
    assert check_fields(string_field, ["bogus"], toml_data) == 0


def test_convert_poetry_to_pep508():
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


def test_fill_version_to_three_parts():
    assert VersionUtils.fill_version_to_three_parts("") == "0.0.0"
    assert VersionUtils.fill_version_to_three_parts("0") == "0.0.0"
    assert VersionUtils.fill_version_to_three_parts("0.0") == "0.0.0"
    assert VersionUtils.fill_version_to_three_parts("0.0.0") == "0.0.0"


def test_dependency_extras():
    expected: str = str(Requirement("unicorn[gevent]>=20.1.0"))
    results: set[Requirement] = to_poetry_requirements({"unicorn": {"extras": ["gevent"], "version": ">=20.1"}})
    assert len(results) == 1, "one pep508 requirement generated"
    assert expected == str(results.pop()), "unicorn[gevent]>=20.1.0"


def test_dependency_two_extras():
    expected: str = str(Requirement("unicorn[gevent,mysql]>=20.1.1"))
    results: set[Requirement] = to_poetry_requirements(
        {"unicorn": {"extras": ["gevent", "mysql"], "version": ">=20.1.1"}}
    )
    assert len(results) == 1, "one pep508 requirement generated"
    assert expected == str(results.pop()), "unicorn[gevent]>=20.1.1"


def test_optional_dependency():
    expected: str = str(Requirement("unicorn>=20.1.0"))
    results: set[Requirement] = to_poetry_requirements({"unicorn": {"optional": "true", "version": ">=20.1"}})
    assert len(results) == 1, "one pep508 requirement generated"
    assert expected == str(results.pop()), "unicorn>=20.1.0, optional=true"


def test_git_dependency():
    expected: str = str(Requirement("check-pyproject@ git+https://github.com:royw/check_pyproject.git"))
    results: set[Requirement] = to_poetry_requirements(
        {"check-pyproject": {"git": "git@github.com:royw/check_pyproject.git"}}
    )
    assert len(results) == 1, "one pep508 requirement generated"
    assert expected == str(results.pop()), "check-pyproject@git+https://github.com:royw/check_pyproject.git"


def test_caret_requirement_to_pep508():
    assert str(SpecifierSet(">=1.2.3")) == caret_requirement_to_pep508(
        "^1.2.3"[1:], max_bounds=False
    ), "^1.2.3 max_bounds=False"
    assert str(SpecifierSet(">=1.2.3,<2.0.0")) == caret_requirement_to_pep508(
        "^1.2.3"[1:], max_bounds=True
    ), "^1.2.3 max_bounds=True"
