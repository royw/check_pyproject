import sys
import unittest
from pathlib import Path
from typing import Any

import tomllib
from loguru import logger
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet

from check_pyproject.__main__ import LOGURU_SHORT_FORMAT
from check_pyproject.check_pyproject_toml import (
    check_fields,
    convert_poetry_to_pep508,
    string_field,
    to_poetry_requirements,
    validate_pyproject_toml_file,
)
from check_pyproject.poetry_requirement import caret_requirement_to_pep508
from check_pyproject.version_utils import VersionUtils

logger.remove(None)
logger.add(sys.stderr, level="DEBUG", format=LOGURU_SHORT_FORMAT)


class CheckPyProjectTomlTestCase(unittest.TestCase):
    def test_all_good_pyproject(self):
        number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "good_pyproject.toml")
        self.assertEqual(0, number_of_problems)

    def test_optional_deps_pyproject(self):
        number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "optional_deps_pyproject.toml")
        self.assertEqual(0, number_of_problems)

    def test_all_bad_pyproject(self):
        number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "bad_pyproject.toml")
        self.assertEqual(14, number_of_problems)

    def test_bad_python_pyproject(self):
        number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "bad_python_pyproject_1.toml")
        self.assertEqual(1, number_of_problems)

    def test_bad_python_pyproject_2(self):
        number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "bad_python_pyproject_2.toml")
        self.assertEqual(1, number_of_problems)

    def test_bad_python_pyproject_3(self):
        number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "bad_python_pyproject_3.toml")
        self.assertEqual(0, number_of_problems)

    def test_mixed_pyproject(self):
        number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "mixed_pyproject.toml")
        self.assertEqual(6, number_of_problems)

    def test_nonexistent_file(self):
        number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent / "xyzzy")  # :-)
        self.assertEqual(1, number_of_problems)

    def test_invalid_pyproject_file(self):
        # ASSUMES README.md is in the parent directory of the directory of this test
        # i.e.: ./this_test.py and ../README.md
        number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent.parent / "README.md")
        self.assertEqual(1, number_of_problems)

    def test_directory(self):
        # ASSUMES pyproject.toml is in the parent directory of the directory of this test
        # i.e.: ./this_test.py so ../pyproject.toml
        number_of_problems: int = validate_pyproject_toml_file(Path(__file__).parent.parent)
        self.assertEqual(1, number_of_problems)

    def test_missing_field(self):
        with open(Path(__file__).parent / "good_pyproject.toml", encoding="utf-8") as f:
            toml_data: dict[str, Any] = tomllib.loads(f.read())
        self.assertTrue(check_fields(string_field, ["bogus"], toml_data) == 0)

    def test_convert_poetry_to_pep508(self):
        # ref: https://python-poetry.org/docs/dependency-specification/
        # Caret requirements
        self.assertEqual(
            SpecifierSet(">=1.2.3, <2.0.0"), SpecifierSet(convert_poetry_to_pep508("^1.2.3")), msg="^1.2.3"
        )
        self.assertEqual(SpecifierSet(">=1.2.0, <2.0.0"), SpecifierSet(convert_poetry_to_pep508("^1.2")), msg="^1.2")
        self.assertEqual(SpecifierSet(">=1.0.0, <2.0.0"), SpecifierSet(convert_poetry_to_pep508("^1")), msg="^1")
        self.assertEqual(
            SpecifierSet(">=0.2.3, <0.3.0"), SpecifierSet(convert_poetry_to_pep508("^0.2.3")), msg="^0.2.3"
        )
        self.assertEqual(
            SpecifierSet(">=0.0.3, <0.0.4"), SpecifierSet(convert_poetry_to_pep508("^0.0.3")), msg="^0.0.3"
        )
        self.assertEqual(SpecifierSet(">=0.0.0, <0.1.0"), SpecifierSet(convert_poetry_to_pep508("^0.0")), msg="^0.0")
        self.assertEqual(SpecifierSet(">=0.0.0, <1.0.0"), SpecifierSet(convert_poetry_to_pep508("^0")), msg="^0")

        # Tilde requirements
        self.assertEqual(
            SpecifierSet(">=1.2.3, <1.3.0"), SpecifierSet(convert_poetry_to_pep508("~1.2.3")), msg="~1.2.3"
        )
        self.assertEqual(SpecifierSet(">=1.2.0, <1.3.0"), SpecifierSet(convert_poetry_to_pep508("~1.2")), msg="~1.2")
        self.assertEqual(SpecifierSet(">=1.0.0, <2.0.0"), SpecifierSet(convert_poetry_to_pep508("~1")), msg="~1")

        # Wildcard requirements
        self.assertEqual(SpecifierSet(">=0.0.0"), SpecifierSet(convert_poetry_to_pep508("*")), msg="*")
        self.assertEqual(SpecifierSet(">=1.0.0, <2.0.0"), SpecifierSet(convert_poetry_to_pep508("1.*")), msg="1.*")
        self.assertEqual(SpecifierSet(">=1.2.0, <1.3.0"), SpecifierSet(convert_poetry_to_pep508("1.2.*")), msg="1.2.*")

        # Inequality requirements
        self.assertEqual(SpecifierSet(">=1.2.0"), SpecifierSet(convert_poetry_to_pep508(">= 1.2.0")), msg=">= 1.2.0")
        self.assertEqual(SpecifierSet(">1.0.0"), SpecifierSet(convert_poetry_to_pep508("> 1")), msg="> 1")
        self.assertEqual(SpecifierSet("<2.0.0"), SpecifierSet(convert_poetry_to_pep508("< 2")), msg="< 2")
        self.assertEqual(SpecifierSet("!=1.2.4"), SpecifierSet(convert_poetry_to_pep508("!= 1.2.4")), msg="!= 1.2.4")

        # Multiple requirements
        self.assertEqual(
            SpecifierSet(">=1.2.0, !=1.2.4"),
            SpecifierSet(convert_poetry_to_pep508(">= 1.2.0, != 1.2.4")),
            msg=">= 1.2.0, != 1.2.4",
        )
        self.assertEqual(
            SpecifierSet(">=1.2.0, <1.5.0"),
            SpecifierSet(convert_poetry_to_pep508(">= 1.2, < 1.5")),
            msg=">= 1.2, < 1.5",
        )

        # Exact requirements
        self.assertEqual(SpecifierSet("==1.2.3"), SpecifierSet(convert_poetry_to_pep508("==1.2.3")), msg="==1.2.3")
        self.assertEqual(SpecifierSet("==1.2.0"), SpecifierSet(convert_poetry_to_pep508("==1.2")), msg="==1.2")
        self.assertEqual(SpecifierSet("==1.0.0"), SpecifierSet(convert_poetry_to_pep508("==1")), msg="==1")

        # note, packaging module does not allow bare version numbers, ex: "1.2.3"

    def test_fill_version_to_three_parts(self):
        self.assertEqual("0.0.0", VersionUtils.fill_version_to_three_parts(""))
        self.assertEqual("0.0.0", VersionUtils.fill_version_to_three_parts("0"))
        self.assertEqual("0.0.0", VersionUtils.fill_version_to_three_parts("0.0"))
        self.assertEqual("0.0.0", VersionUtils.fill_version_to_three_parts("0.0.0"))

    def test_dependency_extras(self):
        expected: str = str(Requirement("unicorn[gevent]>=20.1.0"))
        results: set[Requirement] = to_poetry_requirements({"unicorn": {"extras": ["gevent"], "version": ">=20.1"}})
        self.assertTrue(len(results) == 1)
        self.assertEqual(expected, str(results.pop()), msg="unicorn[gevent]>=20.1.0")

    def test_dependency_two_extras(self):
        expected: str = str(Requirement("unicorn[gevent,mysql]>=20.1.1"))
        results: set[Requirement] = to_poetry_requirements(
            {"unicorn": {"extras": ["gevent", "mysql"], "version": ">=20.1.1"}}
        )
        self.assertTrue(len(results) == 1)
        self.assertEqual(expected, str(results.pop()), msg="unicorn[gevent]>=20.1.1")

    def test_optional_dependency(self):
        expected: str = str(Requirement("unicorn>=20.1.0"))
        results: set[Requirement] = to_poetry_requirements({"unicorn": {"optional": "true", "version": ">=20.1"}})
        self.assertTrue(len(results) == 1)
        self.assertEqual(expected, str(results.pop()), msg="unicorn>=20.1.0, optional=true")

    def test_git_dependency(self):
        expected: str = str(Requirement("check-pyproject@ git+https://github.com:royw/check_pyproject.git"))
        results: set[Requirement] = to_poetry_requirements(
            {"check-pyproject": {"git": "git@github.com:royw/check_pyproject.git"}}
        )
        self.assertTrue(len(results) == 1)
        self.assertEqual(
            expected, str(results.pop()), msg="check-pyproject@git+https://github.com:royw/check_pyproject.git"
        )

    def test_caret_requirement_to_pep508(self):
        self.assertEqual(
            str(SpecifierSet(">=1.2.3")),
            caret_requirement_to_pep508("^1.2.3"[1:], max_bounds=False),
            msg="^1.2.3 max_bounds=False",
        )

        self.assertEqual(
            str(SpecifierSet(">=1.2.3,<2.0.0")),
            caret_requirement_to_pep508("^1.2.3"[1:], max_bounds=True),
            msg="^1.2.3 max_bounds=True",
        )


if __name__ == "__main__":
    unittest.main()
