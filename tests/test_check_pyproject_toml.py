import unittest
from pathlib import Path

from check_pyproject.check_pyproject_toml import validate_pyproject_toml_file, convert_poetry_to_pep508


class CheckPyProjectTomlTestCase(unittest.TestCase):
    def test_all_good_pyproject(self):
        number_of_problems = validate_pyproject_toml_file(Path.cwd() / "tests" / "good_pyproject.toml")
        self.assertEqual(0, number_of_problems)

    def test_all_bad_pyproject(self):
        number_of_problems = validate_pyproject_toml_file(Path.cwd() / "tests" / "bad_pyproject.toml")
        self.assertEqual(14, number_of_problems)

    def test_mixed_pyproject(self):
        number_of_problems = validate_pyproject_toml_file(Path.cwd() / "tests" / "mixed_pyproject.toml")
        self.assertEqual(6, number_of_problems)

    def test_nonexistent_file(self):
        number_of_problems = validate_pyproject_toml_file(Path.cwd() / "xyzzy")  # :-)
        self.assertEqual(1, number_of_problems)

    def test_invalid_pyproject_file(self):
        number_of_problems = validate_pyproject_toml_file(Path.cwd() / "README.md")
        self.assertEqual(1, number_of_problems)

    def test_directory(self):
        number_of_problems = validate_pyproject_toml_file(Path.cwd())
        self.assertEqual(1, number_of_problems)

    def test_convert_poetry_to_pep508(self):
        # ref: https://python-poetry.org/docs/dependency-specification/
        # Caret requirements
        self.assertEqual(convert_poetry_to_pep508("^1.2.3"), ">=1.2.3, <2.0.0", msg="^1.2.3")
        self.assertEqual(convert_poetry_to_pep508("^1.2"), ">=1.2.0, <2.0.0", msg="^1.2")
        self.assertEqual(convert_poetry_to_pep508("^1"), ">=1.0.0, <2.0.0", msg="^1")
        self.assertEqual(convert_poetry_to_pep508("^0.2.3"), ">=0.2.3, <0.3.0", msg="^0.2.3")
        self.assertEqual(convert_poetry_to_pep508("^0.0.3"), ">=0.0.3, <0.0.4", msg="^0.0.3")
        self.assertEqual(convert_poetry_to_pep508("^0.0"), ">=0.0.0, <0.1.0", msg="^0.0")
        self.assertEqual(convert_poetry_to_pep508("^0"), ">=0.0.0, <1.0.0", msg="^0")

        # Tilde requirements
        self.assertEqual(convert_poetry_to_pep508("~1.2.3"), ">=1.2.3, <1.3.0", msg="~1.2.3")
        self.assertEqual(convert_poetry_to_pep508("~1.2"), ">=1.2.0, <1.3.0", msg="~1.2")
        self.assertEqual(convert_poetry_to_pep508("~1"), ">=1.0.0, <2.0.0", msg="~1")

        # Wildcard requirements
        self.assertEqual(convert_poetry_to_pep508("*"), ">=0.0.0", msg="*")
        self.assertEqual(convert_poetry_to_pep508("1.*"), ">=1.0.0, <2.0.0", msg="1.*")
        self.assertEqual(convert_poetry_to_pep508("1.2.*"), ">=1.2.0, <1.3.0", msg="1.2.*")

        # Inequality requirements
        self.assertEqual(convert_poetry_to_pep508(">= 1.2.0"), ">=1.2.0", msg=">= 1.2.0")
        self.assertEqual(convert_poetry_to_pep508("> 1"), ">1.0.0", msg="> 1")
        self.assertEqual(convert_poetry_to_pep508("< 2"), "<2.0.0", msg="< 2")
        self.assertEqual(convert_poetry_to_pep508("!= 1.2.4"), "!=1.2.4", msg="!= 1.2.4")

        # Multiple requirements
        self.assertEqual(convert_poetry_to_pep508(">= 1.2.0 != 1.2.4"), ">=1.2.0 !=1.2.4", msg=">= 1.2.0 != 1.2.4")
        self.assertEqual(convert_poetry_to_pep508(">= 1.2, < 1.5"), ">=1.2.0, <1.5.0", msg=">= 1.2, < 1.5")

        # Exact requirements
        self.assertEqual(convert_poetry_to_pep508("==1.2.3"), "==1.2.3", msg="==1.2.3")
        self.assertEqual(convert_poetry_to_pep508("==1.2"), "==1.2.0", msg="==1.2")
        self.assertEqual(convert_poetry_to_pep508("==1"), "==1.0.0", msg="==1")
        self.assertEqual(convert_poetry_to_pep508("1.2.3"), "1.2.3", msg="1.2.3")
        self.assertEqual(convert_poetry_to_pep508("1.2"), "1.2.0", msg="1.2")
        self.assertEqual(convert_poetry_to_pep508("1"), "1.0.0", msg="1")


if __name__ == "__main__":
    unittest.main()
