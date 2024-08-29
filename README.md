<!--
SPDX-FileCopyrightText: 2024 Roy Wright

SPDX-License-Identifier: MIT
-->

# Check PyProject

[![PyPI - Version](https://img.shields.io/pypi/v/check_pyproject.svg)](https://pypi.org/project/check_pyproject)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/check_pyproject.svg)](https://pypi.org/project/check_pyproject)

---

## Table of Contents

<!-- TOC -->

- [Check PyProject](#check-pyproject)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Usage](#usage)
  - [Installation](#installation)
    - [PyPI Installation](#pypi-installation)
    - [Development installation](#development-installation)
      - [Development Prerequisites](#development-prerequisites)
  - [License](#license)
  - [References](#references)
  <!-- TOC -->

## Overview

Checks that [project] and [tool.poetry] tables are mostly in-sync in the
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
tables, are roughly in-sync.

## Usage

The default usage will check the pyproject.toml file in the current directory
showing everything it is checking. You probably ought to run this at least once
to see what fields check_pyproject does not check. The last line is the number
of issues found.

    ➤ check_pyproject
    Checking: "pyproject.toml"
    Reading pyproject.toml file: pyproject.toml
    "name" found in both [project] and [tool.poetry]
    "description" found in both [project] and [tool.poetry]
    "readme" found in both [project] and [tool.poetry]
    "version" found in both [project] and [tool.poetry]
    "scripts" found in both [project] and [tool.poetry]
    "urls" found in both [project] and [tool.poetry]
    "keywords" found in both [project] and [tool.poetry]
    "classifiers" found in both [project] and [tool.poetry]
    "authors" found in both [project] and [tool.poetry]
    "maintainers" found in both [project] and [tool.poetry]
    Fields not checked in [project]:  ['dynamic', 'license', 'requires-python']
    Fields not checked in [tool.poetry]:  ['documentation', 'homepage', 'include', 'license', 'packages', 'repository']
    Note that the license tables have completely different formats between
    [project] (takes either a file or a text attribute of the actual license and [tool.poetry] (takes the name of the license), so both must be manually set.
    Check pyproject.toml file: pyproject.toml => 0 problems detected.

You can run check_pyproject quietly, where just issues are emitted. Here's an
example where you specify the pyproject.toml file and find a version mismatch:

    ➤ check_pyproject --quiet pyproject.toml
    Values do not match between project.version and tool.poetry.version.
    Differences:
    "0.1.1"
    vs.
    "0.1.1a1"

The most common issue check_pyproject finds is adding a dependency in only one
table:

    ➤ check_pyproject --quiet
    Dependencies "test" Differences:
    project: []
    vs
    poetry: ["pytest-xdist[psutil]<4.0.0,>=3.6.1"]

Notice that the poetry version has been converted from the poetry syntax:

    pytest-xdist = {extras = ["psutil"], version = "^3.6.1"}

to PEP-508 which is what the project table requires, facilitating copying the
dependency in check_pyproject's output, `"pytest-xdist[psutil]<4.0.0,>=3.6.1"`,
to the project table's appropriate dependency table.

## Installation

### PyPI Installation

`pip install check_pyproject`

### Development installation

#### Development Prerequisites

- Install the task manager: [Task](https://taskfile.dev/)
- Optionally install [pyenv-installer](https://github.com/pyenv/pyenv-installer)

  - Install dependent pythons, example:

    `pyenv local 3.11.9 3.12.3`

  _Note you may need to install some libraries for the pythons to compile
  cleanly._ _For example on ubuntu (note I prefer `nala` over `apt`):_

  `sudo nala install tk-dev libbz2-dev libreadline-dev libsqlite3-dev lzma-dev python3-tk libreadline-dev`

- Recommended to upgrade pip to latest.
- Optionally install [Poetry](https://python-poetry.org/)
- Optionally install [Hatch](https://hatch.pypa.io/)
- Optionally install [setuptools](https://setuptools.pypa.io/)
  - Install [build](https://build.pypa.io/)

Install the package using your favorite dev tool. Examples:

- `git clone git@github.com:royw/check_pyproject.git`
- `cd check_pyproject`
- `task init`
- `task make`

_Note, `task init` will run `git init .`, `git add` the initial project files,
and do a `git commit`. If you are using another VCS, please first edit the init
task in the `Taskfile.yaml` file._

See the [Developer README](DEV-README.md) for detailed information on the
development environment.

## License

`check_pyproject` is distributed under the terms of the
[MIT](https://spdx.org/licenses/MIT.html) license.

## References

- The [Python Packaging User Guide](https://packaging.python.org/en/latest)
- The
  [pyproject.toml specification](https://pypi.python.org/pypi/pyproject.toml)
- The [Poetry pyproject.toml metadata](https://python-poetry.org/docs/pyproject)
- [pip documentation](https://pip.pypa.io/en/stable/)
- [Setuptools](https://setuptools.pypa.io/)
