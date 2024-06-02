# Check PyProject

Check that [project] and [tool.poetry] tables are in-sync in the pyproject.toml file.

The Python Packaging User Guide now specifies pyproject.toml metadata.

Poetry <2.0 predates the metadata specification and instead used the then current standard of
[tool.poetry] table.  While there is a lot of overlap, there are some differences (ex. dependency package specifiers).
Poetry 2.0 will support PyPA pyproject.toml specification (formerly PEP 621) which will obsolete
this utility.

So if your project uses poetry and any other tool that requires the current pyproject.toml metadata, or you
are prepping for Poetry 2.0 and do not want to use the development version of Poetry.
then you need to manually maintain sync between [project] and [tool.poetry] tables.

This tool checks that overlapping metadata, between [project] and [tool.poetry] tables, is roughly in-sync.

## Prerequisites

* Install the task manager: [taskfile](https://taskfile.dev/)
* Install [Poetry](https://python-poetry.org/)
* Optionally install pyenv-installer.  https://github.com/pyenv/pyenv-installer
  * Install dependent pythons, example:
  
    `pyenv local 3.11.9 3.12.3`

    *Note you may need to install some libraries for the pythons to compile cleanly.* 
    *For example on ubuntu (note I prefer `nala` over `apt`):*

  `sudo nala install tk-dev libbz2-dev libreadline-dev libsqlite3-dev lzma-dev python3-tk libreadline-dev`

## Usage

Two usages:

1. Install the package using your favorite dev tool.  Examples:
   
   - `git clone git@github.com:royw/check_pyproject.git`
   - `cd check_pyproject`
   - `task init`
   - `task build`
   - Install check\_pyproject:  `pip install dest/check_pyproject-*.whl`
   
    then cd to your project and run: `check_pyproject`

2. Or just copy src/check\_pyproject\_toml.py to your project's bin directory and run it:

    `python ./bin/check_pyproject_toml.py`

## References

- The [Python Packaging User Guide](https://packaging.python.org/en/latest)
- The [pyproject.toml specification](https://pypi.python.org/pypi/pyproject.toml)
- The [Poetry pyproject.toml metadata](https://python-poetry.org/docs/pyproject)

### Build tools
- [loguru](https://loguru.readthedocs.io) improved logging.
- [pytest](https://docs.pytest.org) unit testing.
- [pathvalidate](https://pathvalidate.readthedocs.io)
- [tox](https://tox.wiki) multiple python testing. 
- [radon](https://radon.readthedocs.io) code metrics.
- [Ruff](https://docs.astral.sh/ruff/) an extremely fast Python linter and code formatter, written in Rust.
- [FawltyDeps](https://github.com/tweag/FawltyDeps) unused dependency checker.
 
### Documentation tools 
- [MkDocs](https://www.mkdocs.org/)
- [mkdocs-gen-files](https://github.com/oprypin/mkdocs-gen-files) Plugin for MkDocs to programmatically generate documentation pages during the build
- [mkdocs-literate-nav](https://github.com/oprypin/mkdocs-literate-nav) Plugin for MkDocs to specify the navigation in Markdown instead of YAML
- [mkdocs-section-index](https://github.com/oprypin/mkdocs-section-index) Plugin for MkDocs to allow clickable sections that lead to an index page
- [mkdocstrings](https://mkdocstrings.github.io/) Automatic documentation from sources, for MkDocs.
- [catalog](https://github.com/mkdocs/catalog) Catalog of MkDocs plugins.