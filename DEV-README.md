<!--
SPDX-FileCopyrightText: 2024 Roy Wright

SPDX-License-Identifier: MIT
-->

# Welcome to this project's development environment!

What I'll attempt to do is explain the tool choices, their configuration, and
their interactions. Please note that development environments are a snapshot of
what is working, hopefully best working, as of now. Undoubtedly better tools,
different processes, and just personal preferences will change. So the best I
can hope for is preparing you for the start of this voyage! ;-)

<!-- TOC -->

- [Welcome to this project's development environment!](#welcome-to-this-projects-development-environment)
  - [Background](#background)
    - [In the beginning](#in-the-beginning)
    - [Today](#today)
  - [Development Environment Requirements](#development-environment-requirements)
  - [20,000 foot view](#20000-foot-view-)
    - [Task](#task)
    - [Taskfile\*.yml](#taskfileyml)
  - [Under the hood](#under-the-hood) _ [Top level tables](#top-level-tables) _
  [check_pyproject](#check_pyproject) _
  [virtual environments](#virtual-environments) _ [testing](#testing) _
  [tox](#tox) _ [coverage](#coverage) _ [config.toml](#configtoml) _
  [mkdocs](#mkdocs) _ [pre-commit](#pre-commit) _ [poetry.lock](#poetrylock) _
  [reuse](#reuse) _ [git](#git)
  <!-- TOC -->

## Background

When the muse strikes, and it's time to create a new CLI application, I don't
want to spend time setting up the development environment. I just want to jump
into the new project. The current incarnation of my quick start, is a
cookiecutter template, cookiecutter-clibones. Since it had been a few years,
clibones is mostly new, with an updated ApplicationSettings base class (more
later).

### In the beginning

There was a confusing mess loosely referred to as python packaging.

### Today

Things are a lot better. Still some experimenting going on, which is good.

Metadata is consolidating into a single
[pyproject.toml](https://pypi.python.org/pypi/pyproject.toml) file. Tool
configurations are also migrating to `pyproject.toml`. For the current state of
packaging, see [Python Packaging User Guide](https://packaging.python.org/) from
the [Python Packaging Authority](https://www.pypa.io) (PyPA).

Poetry is probably the leading package manager for the past few years. Alas,
times change. PyPA has filled out the Project definition in `pyproject.toml`.
Multiple build backends are easily supported. Newer package managers are out,
like [hatch](https://hatch.pypa.io/),
[pdm](https://packaging.python.org/en/latest/key_projects/#pdm),
[flit](https://packaging.python.org/en/latest/key_projects/#flit). Even
[Setuptools](https://setuptools.pypa.io/) is staying in the race.

So I decided this development environment will support both Poetry and Hatch.
Poetry is opinionated, uses non-standard revision syntax, and is a little dated
on its `pyproject.toml` usage (most settings - at least until poetry version 2
is released) are in [tool.poetry]. Hatch is hard core standards based, even if
they have to wait for the standard to be adopted. Should be interesting...

One more detail, I'm very much old school. The proper way to build a project is:

    config
    make
    make test
    make install

Nice and simple. Definitely not python package manager style. Luckily there are
tools available to help convert package manager commands into something simpler,
more elegant. I'm currently settled on [Task](https://taskfile.dev/).

Ok, final detail, I have spent years hating Sphinx. If you don't understand why,
then you've been lucky enough not to have to use sphinx. The great news is
[MkDocs](https://www.mkdocs.org/), a markdown base documentation tool, works
fantastic!

## Development Environment Requirements

Support:

- [Poetry](https://python-poetry.org/)
- [Hatch](https://hatch.pypa.io/)
- [PyCharm](https://www.jetbrains.com/pycharm/)
- [MkDocs](https://www.mkdocs.org/)
- [pytest](https://docs.pytest.org)
- [git](https://git-scm.com/)
  - [pre-commit](https://pre-commit.com/)
- [pyenv-installer](https://github.com/pyenv/pyenv-installer)
- testing multiple versions of python
  - [tox](https://tox.wiki) for poetry,
  - hatch matrices
- [radon](https://radon.readthedocs.io) code metrics
- [Ruff](https://docs.astral.sh/ruff/) code formatting
- Both [Ruff](https://docs.astral.sh/ruff/) and
  [MyPy](https://www.mypy-lang.org/) linters

## 20,000 foot view

### Task

Let's start with just running task:

    ➤ task
    task: [default] task --list
    task: Available tasks for this project:
    * build:                  Build the project.
    * build-docs:             Build the documentation.
    * check-licenses:         Check that all dependency licenses are acceptable for this project.
    * check-pyproject:        Check the consistency between poetry and hatch in the pyproject.toml file.
    * clean:                  Remove virtual environments and generated files.
    * coverage:               Run the unit tests with coverage.
    * docs:                   Create the project documentation and open in the browser.
    * format:                 Check and reformat the code to a coding standard.
    * lint:                   Perform static code analysis.
    * main:                   Run the __main__ module code, passing arguments to the module.  Example: task main -- --version
    * metrics:                Analyze the code.
    * pre-commit:             Must pass before allowing version control commit.
    * serve-docs:             Start the documentation server and open browser at localhost:8000.
    * switch-to-hatch:        Switch development to use hatch instead of poetry.
    * switch-to-poetry:       Switch development to use poetry instead of hatch.
    * tests:                  Run the unit tests for the supported versions of python.
    * version:                Run the project, having it return its version.

Cool, so looking over the list I'd guess the first thing I ought to do is:

    ➤ task switch-to-hatch

because I like hatch, then let's just go for broke and:

    ➤ task build

Nice. Now the build task is the main rinse and repeat task, i.e., build it,
correct errors, build it,...

So now the project is building clean, whoooop! Before proceeding, let's take a
look at what the build task does:

    ➤ task build --summary
    task: build

    Build the project

    Format the project, check for code quality, check for compliance,
    perform unit testing, build distributables, build documentation,
    and run the application to display its version.

    commands:
     - Task: show-env
     - Task: format
     - Task: lint
     - pre-commit run --all-files
     - hatch -e dev build
     - Task: update-venv
     - Task: check-licenses
     - Task: coverage
     - Task: metrics
     - Task: build-docs
     - Task: version

Let's remove the tasks ran by build from the available task list:

    * check-pyproject:        Check the consistency between poetry and hatch in the pyproject.toml file.
    * clean:                  Remove virtual environments and generated files.
    * docs:                   Create the project documentation and open in the browser.
    * main:                   Run the __main__ module code, passing arguments to the module.  Example: task main -- --version
    * pre-commit:             Must pass before allowing version control commit.
    * serve-docs:             Start the documentation server and open browser at localhost:8000.
    * switch-to-hatch:        Switch development to use hatch instead of poetry.
    * switch-to-poetry:       Switch development to use poetry instead of hatch.
    * tests:                  Run the unit tests for the supported versions of python.

and look at pre-commit task which is invoked in .pre-commit-config.yaml when ran
by pre-commit in the build task.

    ➤ task pre-commit --summary
    task: pre-commit

    Must pass before allowing version control commit.

    commands:
     - Task: check-pyproject
     - Task: tests

Removing these tasks from the available task list:

    * clean:                  Remove virtual environments and generated files.
    * docs:                   Create the project documentation and open in the browser.
    * main:                   Run the __main__ module code, passing arguments to the module.  Example: task main -- --version
    * serve-docs:             Start the documentation server and open browser at localhost:8000.
    * switch-to-hatch:        Switch development to use hatch instead of poetry.
    * switch-to-poetry:       Switch development to use poetry instead of hatch.

The clean task is pretty self-evident. If you want a totally clean environment,
then running clean followed by a switch task will do the job.

    ➤ task clean
    ➤ task switch-to-poetry

Now take a look at the docs task:

    ➤ task docs --summary
    task: docs

    Create the project documentation and open in the browser.

    commands:
     - Task: build-docs
     - Task: serve-docs

Note that build-docs is included in the build task, so you might want to just
run `task serve-docs` and examine your documentation. Now if you were in a
documentation editing phase, then the `task docs` would both build and show the
built documentation.

And that leaves us with the main task, which is just a shortcut for running the
project in the project managers virtual environment. Try it:

    ➤ task main -- --help

### Taskfile\*.yml

Last topic on task, there are three task files:

    ➤ ls -l taskfile*
    -rw-rw-r-- 1 royw royw 5895 Jul 11 13:14 Taskfile-hatch.yml
    -rw-rw-r-- 1 royw royw 5333 Jul 11 12:19 Taskfile-poetry.yml
    lrwxrwxrwx 1 royw royw   18 Jul 10 14:12 Taskfile.yml -> Taskfile-hatch.yml

If you compare `Taskfile-hatch.yml` and `Taskfile-poetry.yml` you will notice
they are pretty similar, just using the appropriate hatch or poetry commands.
The symbolically linked `Taskfile.yml` is set with the `switch-to-*` tasks.

## Under the hood

Let's start with the mother of all config files, `pyproject.toml`. Yes,
`pyproject.toml` is intended to eventually hold all the configurations for all
of a project's development tools (ex: pytest, pylint, ruff,...), not just the
package managers.

### Top level tables

For practical purposes, `pyproject.toml` has three top level tables:

- build-system
- project
- tool

The `build-system` specifies which build backend is in use by the project. This
table is controlled with the `switch-to-*` tasks.

The `project` contains the project metadata and dependencies that are used by
pretty much all tools except poetry which keeps the metadata in `tools.poetry`
(current plans are for poetry version 2 to switch to using the `project` table -
fingers crossed).

And the `tool` table contains everything else. The naming convention is
`tool.{name}` where name is the tool/utility name (ex: `tool.ruff` for the ruff
tool's configuration).

### check_pyproject

A lot of the `tool.poetry` is now duplicated in the current `project` table
(giving poetry due credit, when poetry was created, these fields were not
defined in the project table, and therefore poetry correctly used `tool.poetry`
table). As of today, we have to deal with the pain of duplicated data in
`pyproject.toml`.

Therefore, I created `check_pyproject` utility that checks that duplicated
fields in `project` and `tool.poetry` tables have equivalent values. Equivalent
is used intentionally here as, for example, `project` dependencies use PEP 508
specifiers while poetry has their own tilde notation, which `check_pyproject`
translates to PEP 508 for comparison purposes. There are a few leftover fields
that cannot be compared, for example license, and are emitted as a warning to
the user to manually verify.

`check_pyproject` doesn't try to fix any problems. Its main purpose is to catch
issues that may creep in. For example: say you are using poetry, and naturally
do a `poetry add --group dev foo`. `check_pyproject` will point out that
`project.optional-dependencies.dev` table does not have 'foo' while
`tool.poetry.group.dev.dependencies` has 'foo>=0.1.1<0.2.0', expecting you to
simply copy the dependency specifier and paste it into the correct project
table.

### virtual environments

Both poetry and hatch make use of virtual environments. To enable both poetry
and hatch to share the same virtual environment and to share the same virtual
environment with PyCharm, the project's .venv/ virtual environment is used.

For poetry, the `task switch-to-poetry` sets the virtualenvs.in-project config
to true.

    ➤ poetry config virtualenvs.in-project true

For hatch, the type and path are set in the default environment which the other
environments inherit from.

    [tool.hatch.envs.default]
    type = "virtual"
    path = ".venv"

Finally, for pycharm:

    Settings - Project - Python Interpreter - Virtual Environment - Existing - Location:  .venv

Note, if you `task clean`, which deletes the .venv/ directory, then you ought to
recreate the virtual environment before using pycharm. The easiest is to just do
a `task build`.

### src/ layout

The file structure is:

    .
    .venv/        # virtual environment shared by: hatch, poetry, & IDE
    .reuse/       # generated reuse templates
    dist/         # generated distribution files
    docs/         # documentation source files
    LICENSES/     # license files
    metrics/      # generated metrics reports
    node_modules  # generated by pre-commit
    scripts/      # project build scripts
    site/         # generated documentation
    src/          # project source files
    tests/        # unit test files
    .coverage     # generated coverage file
    .gitignore    # files not to check in to git
    .pre-commit-config-yaml   # pre-commit config file
    .python-version           # generated by pyenv list of python versions
    config.toml               # generated
    DEV-README.md             # this file
    mkdocs.yml                # mkdocs documentation system config file
    poetry.lock               #
    README.md                 # Standard README file in markdown format
    reuse.spdx                #
    Taskfile.yml              # link to active taskfile
    Taskfile-hatch.yml        # hatch based taskfile
    Taskfile-poetry.yml       # poetry based taskfile
    tox.ini                   # tox configuration file

### testing

Pytest is used for unit testing. The test cases are in the `tests/` directory.
Configuration is in `pyproject.toml`, `tool.pytest.ini_options` table instead of
the traditional `pytest.ini` file.

#### tox

#### coverage

### config.toml

### mkdocs

- docs/
- site/

### pre-commit

- .pre-commit-config.yaml

### poetry.lock

### reuse

### git
