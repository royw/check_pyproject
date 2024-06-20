<!--
SPDX-FileCopyrightText: 2024 Roy Wright
SPDX-License-Identifier: MIT
-->

# Check PyProject

[![PyPI - Version](https://img.shields.io/pypi/v/check_pyproject.svg)](https://pypi.org/project/check_pyproject)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/check_pyproject.svg)](https://pypi.org/project/check_pyproject)

-----

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Workflows](#workflows)
  - [Tasks](#tasks)
  - [Switching between Poetry and Hatch](#switching-between-poetry-and-hatch) 
  - [Adding a dependency using poetry](#adding-a-dependency-using-poetry)
  - [Adding a dependency using hatch](#adding-a-dependency-using-hatch)
- [License](#license)
- [References](#references)
  - [Build tools](#build-tools)
    - [FawltyDeps](#fawltydeps)
  - [Documentation tools](#documentation-tools)

## Overview

Check that [project] and [tool.poetry] tables are in-sync in the
`pyproject.toml` file.

The Python Packaging User Guide now specifies `pyproject.toml` metadata.

Poetry <2.0 predates the metadata specification and instead used the then
current standard of [tool.poetry] table. While there is a lot of overlap, there
are some differences (ex. dependency package specifiers). Poetry 2.0 will
support PyPA pyproject.toml specification (formerly PEP 621) which will obsolete
this utility.

So if your project uses poetry and any other tool that requires the current
pyproject.toml metadata, or you are prepping for Poetry 2.0 and do not want to
use the development version of Poetry. then you need to manually maintain sync
between [project] and [tool.poetry] tables.

This tool checks that overlapping metadata, between [project] and [tool.poetry]
tables, is roughly in-sync.

## Prerequisites

* Install the task manager: [Task](https://taskfile.dev/)
* Optionally install [Poetry](https://python-poetry.org/)
* Optionally install [Hatch](https://hatch.pypa.io/)
* Optionally install [pyenv-installer](https://github.com/pyenv/pyenv-installer)
  * Install dependent pythons, example:
  
    `pyenv local 3.11.9 3.12.3`

_Note you may need to install some libraries for the pythons to compile 
cleanly._ _For example on ubuntu (note I prefer `nala` over `apt`):_

  `sudo nala install tk-dev libbz2-dev libreadline-dev libsqlite3-dev lzma-dev python3-tk libreadline-dev`

## Installation

Install the package using your favorite dev tool. Examples:

   - `git clone git@github.com:royw/check_pyproject.git`
   - `cd check_pyproject`
   - `git init .`
   - `git add .`
   - `git commit -m "initial clibones cookie"`
   - `task init`
   - `task build`
   - Install check_pyproject: `pip install dest/check_pyproject-*.whl`

then cd to your project and run: `check_pyproject`

_Note, if you do not initialize git in the new project and add at least the .gitignore file, 
then `reuse` will be unable to honor `.gitignore` and will spew a few errors, causing the build to fail._

## Workflows

### Tasks

The `Taskfile.yml` is used to build your workflow as a set of tasks. The initial
workflow is:

    task clean  # removes all build artifacts (metrics, docs,...)
    task build  # lints, formats, checks pyproject.toml, and generates metrics, performs unit tests,
                  performs tox testing, and creates the package.
    task docs   # creates local documentation, starts a local server, opens the home page of the documents in a browser.
    task main   # launches the application in the poetry environment.

This is a starting off point so feel free to CRUD the tasks to fit your needs,
or not even use it.

### Switching between Poetry and Hatch

Two tasks support switching the build system:

    task switch-to-poetry
    task switch-to-hatch

They set the symbolic link for `Taskfile.yml` to either `Taskfile-poetry.yml`
or `Taskfile-hatch.yml`.
 
And they edit the `build-system` table in the `pyproject.toml` file to
the appropriate back-end.

### Adding a dependency using poetry

Add the dependency using the poetry CLI.

    poetry add --group dev some_tool
    task build

The build ought to fail as the [project] and [tool.poetry] dependencies are now out of sync.  But the
output includes the PEP 508 dependency just added that you can copy and paste into the [project] table's
appropriate dependency.

    task build

Should pass this time.

### Adding a dependency using hatch

Manually edit the `pyproject.toml` file and add the dependency to both the [project] and [tool.poetry] dependency tables.
Then running

    task build

Will show any version specifier mismatches...


## License

`check_pyproject` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## References

- The [Python Packaging User Guide](https://packaging.python.org/en/latest)
- The
  [pyproject.toml specification](https://pypi.python.org/pypi/pyproject.toml)
- The [Poetry pyproject.toml metadata](https://python-poetry.org/docs/pyproject)
- [pip documentation](https://pip.pypa.io/en/stable/)
- [Setuptools](https://setuptools.pypa.io/)

### Build tools

- [loguru](https://loguru.readthedocs.io) improved logging.
- [pytest](https://docs.pytest.org) unit testing.
- [pathvalidate](https://pathvalidate.readthedocs.io)
- [tox](https://tox.wiki) multiple python testing.
- [radon](https://radon.readthedocs.io) code metrics.
- [Ruff](https://docs.astral.sh/ruff/) is an extremely fast Python linter and code formatter, written 
  in Rust.
- [FawltyDeps](https://github.com/tweag/FawltyDeps) is a dependency checker 
  for Python that finds undeclared and/or unused 3rd-party dependencies in 
  your Python project.
- [Reuse](https://reuse.readthedocs.io/) is a tool for compliance with the 
  [REUSE](https://reuse.software/) recommendations.

#### FawltyDeps

This tool does a great job in helping keep bloat out of your project. There is
one small issue with it, it does not distinguish project dependencies from
dev/test/doc/... dependencies. So you have to manually add any new tools to the
used list in your [pyproject.toml], like:

    poetry run fawltydeps --detailed --ignore-unused radon pytest-cov pytest tox fawltydeps mkdocs
        mkdocstrings-python mkdocs-literate-nav mkdocs-section-index ruff mkdocs-material

### Documentation tools

After years of suffering with the complexity of sphinx and RST (the PyPA
recommended documentation tool), this project uses MkDocs and MarkDown.
Whoooooop!

**_Here is a big THANK YOU to the MkDocs team, the plugin teams, and the theme
teams!_**

**_Fantastic!_**

Plugins do a nice job of
[automatic code reference](https://mkdocstrings.github.io/recipes/#automatic-code-reference-pages),
and a fantastic theme from the mkdocs-material team!

Configuration is in the `mkdocs.yml` file and the `docs/` and `scripts/`
directories.

The `task docs` will build the documentation into a static site, `site/`, and
run a server at http://localhost:8000/ and open the page in your browser.

- [MkDocs](https://www.mkdocs.org/) Project documentation with Markdown.
- [mkdocs-gen-files](https://github.com/oprypin/mkdocs-gen-files) Plugin for
  MkDocs to programmatically generate documentation pages during the build
- [mkdocs-literate-nav](https://github.com/oprypin/mkdocs-literate-nav) Plugin
  for MkDocs to specify the navigation in Markdown instead of YAML
- [mkdocs-section-index](https://github.com/oprypin/mkdocs-section-index) Plugin
  for MkDocs to allow clickable sections that lead to an index page
- [mkdocstrings](https://mkdocstrings.github.io/) Automatic documentation from
  sources, for MkDocs.
- [catalog](https://github.com/mkdocs/catalog) Catalog of MkDocs plugins.
- [mkdocs-material](https://squidfunk.github.io/mkdocs-material/) Material
  theme.
