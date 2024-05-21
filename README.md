# Check PyProject

Check that [project] and [tool.poetry] tables are in-sync in the pyproject.toml file.

The Python Packaging User Guide now specifies pyproject.toml metadata.

Poetry predates the metadata specification and instead used the then current standard of
[tool.poetry] table.  While there is a lot of overlap, there are some differences (ex. dependency package specifiers).

So if your project uses poetry and any other tool that requires the current pyproject.toml metadata,
then you need to manually maintain sync between [project] and [tool.poetry] tables.

This tool checks that overlapping metadata, between [project] and [tool.poetry] tables, is roughly in-sync.
 
## Usage

Two usages:

1. Install the package using your favorite dev tool.  Examples:

   - `pip install check_pyproject`
   - `poetry add check_pyproject`

    then just run: `check_pyproject`

2. Or just copy src/check_pyproject_toml.py to your project's bin directory and just run:

    `python ./bin/check_pyproject_toml.py`

# References

- The Python Packaging User Guide can be found here: https://packaging.python.org/en/latest
- The pyproject.toml specification can be found here: https://pypi.python.org/pypi/pyproject.toml
- The Poetry pyproject.toml metadata can be found here: https://python-poetry.org/docs/pyproject