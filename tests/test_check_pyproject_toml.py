import unittest
from pathlib import Path

from check_pyproject.check_pyproject_toml import validate_pyproject_toml_file


class CheckPyProjectTomlTestCase(unittest.TestCase):
    def test_all_good_pyproject(self):
        number_of_problems = validate_pyproject_toml_file(Path.cwd() / "tests" / "good_pyproject.toml")
        self.assertEqual(0, number_of_problems)  # add assertion here

    def test_all_bad_pyproject(self):
        number_of_problems = validate_pyproject_toml_file(Path.cwd() / "tests" / "bad_pyproject.toml")
        self.assertEqual(14, number_of_problems)  # add assertion here

    def test_mixed_pyproject(self):
        number_of_problems = validate_pyproject_toml_file(Path.cwd() / "tests" / "mixed_pyproject.toml")
        self.assertEqual(6, number_of_problems)  # add assertion here


if __name__ == "__main__":
    unittest.main()
