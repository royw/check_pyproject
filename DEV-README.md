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
  - [Getting Started](#getting-started)
  - [20,000 meter view](#20000-meter-view)
    - [Task](#task)
    - [Adding a dependency using poetry](#adding-a-dependency-using-poetry)
    - [Adding a dependency using hatch](#adding-a-dependency-using-hatch)
    - [Summary](#summary)
  - [Under the hood](#under-the-hood)
    - [Top level tables](#top-level-tables)
    - [check_pyproject](#check_pyproject)
    - [virtual environments](#virtual-environments)
    - [src/ layout](#src-layout)
    - [testing](#testing)
      - [tox](#tox)
      - [matrix testing](#matrix-testing)
      - [coverage](#coverage)
    - [lint](#lint)
      - [run-mypy-all-python-versions.sh](#run-mypy-all-python-versionssh)
      - [fail_on_refex_match.sh](#fail_on_refex_matchsh)
    - [mkdocs](#mkdocs)
    - [pre-commit](#pre-commit)
    - [poetry.lock](#poetrylock)
    - [reuse](#reuse)
    - [git](#git)
    - [Build tools](#build-tools)
      - [FawltyDeps](#fawltydeps)
    - [Documentation tools](#documentation-tools)
  - [CLIBones](#clibones) \* [Architecture](#architecture)
  <!-- TOC -->

## Background

When the muse strikes, and it's time to create a new CLI application, I don't
want to spend time setting up the development environment. I just want to jump
into the new project. The current incarnation of my quick start, is a
cookiecutter template, cookiecutter-clibones.

### In the beginning

There was a confusing mess loosely referred to as python packaging. If curious,
a couple of excellent articles by Chris Warrick are:

- [How to improve Python packaging, or why fourteen tools are at least twelve too many](https://chriswarrick.com/blog/2023/01/15/how-to-improve-python-packaging/)
- [Python Packaging, One Year Later: A Look Back at 2023 in Python Packaging](https://chriswarrick.com/blog/2024/01/15/python-packaging-one-year-later/)

### Today

Things are a lot better. Still fractured. Still messy. But some experimenting
going on, which is good.

_"Hope springs eternal in the human breast: Man never is, but always to be
blest."_ - Alexander Pope _"An Essay on Man"_

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

So I decided this development environment will support Poetry, Hatch, and
Setuptools.

Poetry is opinionated, uses non-standard revision syntax, and is a little dated
on its `pyproject.toml` usage (most settings - at least until poetry version 2
is released, are in the `tool.poetry` table).

Hatch is hard core standards based, even if they have to wait for the standard
to be adopted. Should be interesting...

Setuptools, is, well, setuptools. The current "old school" approach (ok, I
remember when they were new...).

One more detail, I'm very much old school (ok, before python existed). The
proper way to build a project is:

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

- [Task](https://taskfile.dev/)
- [Poetry](https://python-poetry.org/)
- [Hatch](https://hatch.pypa.io/)
- [Setuptools](https://setuptools.pypa.io/)
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

## Getting Started

Create the project with (if you want to be able to resync from the template):

    cruft create https://github.com/royw/cookiecutter-clibones

or

    cookiecutter https://github.com/royw/cookiecutter-clibones

then answering the project questions. To use, you need to run:

    cd program_slug         # from the cookiecutter questions
    pyenv local 3.11 3.12   # or whatever python versions you need
    task init
    task build

The framework is now ready for all of your good stuff.

A couple of useful commands:

    task                # shows available tasks
    less Taskfile.yml   # shows the commands that form each task.  Feel free to customize.
    poetry lock         # for when the poetry.lock gets out of sync with pyproject.toml

## 20,000 meter view

### Task

Let's start with just running task:

    ➤ task
    task: [default] task --list
    task: Available tasks for this project:
    * build:                      Build the project.
    * build-docs:                 Build the documentation.
    * check-licenses:             Check that all dependency licenses are acceptable for this project.
    * check-pyproject:            Check the consistency between poetry and hatch in the pyproject.toml file.
    * check-reuse:                Check if project is REUSE compliant.
    * clean:                      Remove virtual environments and generated files.
    * coverage:                   Run the unit tests with coverage.
    * docs:                       Create the project documentation and open in the browser.
    * format:                     Check and reformat the code to a coding standard.
    * init:                       Initialize new project (only run once upon first creation of project).
    * lint:                       Perform static code analysis.
    * lockfiles-disable:          Disable backend to use requirements.txt files managed by pip-compile as lock files.
    * lockfiles-enable:           Enable backend to use requirements.txt files managed by pip-compile as lock files.
    * main:                       Run the __main__ module code, passing arguments to the module.  Example: task main -- --version
    * make:                       Make the project (format, lint, check, build, metrics, docs).
    * make-env:                   Create and update virtual environment
    * metrics:                    Analyze the code.
    * pre-commit:                 Must pass before allowing version control commit.
    * pypi-version:               Get the current version of the given package(s) from pypi and output as PEP508 dependency specifier(s).
    * reuse-disable:              Disable using SPDX reuse for enforcing copyright and license.
    * reuse-enable:               Enable using SPDX reuse for enforcing copyright and license.
    * reuse-lint:                 Perform reuse checks if pyproject.toml: tools.taskfile.reuse is set to "enabled"
    * serve-docs:                 Start the documentation server and open browser at localhost:8000.
    * switch-to-hatch:            Switch development to use hatch.
    * switch-to-poetry:           Switch development to use poetry.
    * switch-to-setuptools:       Switch development to use setuptools.
    * test:                       Run the unit tests for the supported versions of python.
    * update-env:                 Update virtual environment
    * version:                    Run the project, having it return its version.

Cool, so looking over the list I'd guess the first thing I ought to do after
creating the project using cookiecutter is to initialize it:

    ➤ task init

then let's just go for broke and:

    ➤ task make

Seriously, to start a new project:

1. cookiecutter https://github.com/royw/cookiecutter-clibones
2. cd {your-project-name}
3. task init
4. task build
5. optionally: task switch-to-setuptools
6. ...

Now the make task is the main rinse and repeat task, i.e., make it, correct
errors, make it,...

But say I prefer hatch, it is easy to switch:

    ➤ task switch-to-hatch

or maybe setuptools:

    ➤ task switch-to-setuptools

and to switch back to poetry with:

    ➤ task switch-to-poetry

Note, the editing of the pyproject.toml file to support the switch tasks is in
`scripts/swap_build_system.py`.

So now the project is building clean, whoooop! Before proceeding, let's take a
look at what the build task does:

    ➤ task make --summary
    task: make

    Make the project

    Format the project, check for code quality, check for compliance,
    perform unit testing, build distributables, build documentation,
    and run the application to display its version.

    commands:
     - Task: fe:show-env
     - Task: format
     - Task: lint
     - Task: execute-pre-commit
     - Task: fe:build
     - Task: fe:update-env
     - Task: check-licenses
     - Task: coverage
     - Task: metrics
     - Task: build-docs
     - Task: version

Yes, I like my make to do a lot. Feel free to change to your preferences.

Real quick

- `fe:show-env` just prints info about your virtual environment.
- `format` formats your code using ruff and blacken-docs.
- `lint` checks your code for problems.
- `execute-pre-commit` this is the task that pre-commit calls, so doing here too
  reduces blocked commits...
- `fe:build` builds your project using the current front end.
- `fe:update-env` updates your virtual environment. Necessary to make current
  pyproject.toml values available to metadata.
- `check-licenses` useful when using REUSE to catch new files without
  copyright/license header.
- `coverage` runs pytest with coverage with the python specified in
  pyproject.toml.
- `metrics` here's another you may want to customize.
- `build-docs` generates project documentation into `site/`. To view, run
  `task serve-docs` or `task docs`.
- `version` runs your program with a `--version` option. This is a smoke test of
  your program.

Currently `execute-commit` just calls `check-pyproject`.

Taking a look at the docs task:

    ➤ task docs --summary
    task: docs

    Create the project documentation and open in the browser.

    commands:
     - Task: build-docs
     - Task: serve-docs

Note that build-docs is included in the make task, so you might want to just run
`task serve-docs` and examine your documentation. Now if you were in a
documentation editing phase, then the `task docs` would both build and show the
built documentation.

Note: "fe:" prefix stands for "front-end". When you switch development systems
some taskfiles are symbolically linked to `taskfiles/front-end.yaml` and
`taskfiles/front-end-vars.yaml` which contain development system specific tasks
and variables:

    ➤ ls -l taskfiles
    total 24
    lrwxrwxrwx 1 royw royw   15 Aug  7 22:00 front-end-vars.yaml -> hatch-vars.yaml
    lrwxrwxrwx 1 royw royw   10 Aug  7 22:00 front-end.yaml -> hatch.yaml
    -rw-rw-r-- 1 royw royw  568 Aug  7 22:00 hatch-vars.yaml
    -rw-rw-r-- 1 royw royw 2226 Aug  7 22:00 hatch.yaml
    -rw-rw-r-- 1 royw royw  574 Aug  7 22:00 poetry-vars.yaml
    -rw-rw-r-- 1 royw royw 1561 Aug  7 22:00 poetry.yaml
    -rw-rw-r-- 1 royw royw  598 Aug  7 22:00 setuptools-vars.yaml
    -rw-rw-r-- 1 royw royw 2294 Aug  7 22:00 setuptools.yaml

The main `Taskfile.yaml` loads the `front-end*.yaml` files into the "fe:"
namespace. You will probably very seldom, if ever, run "fe:" tasks directly.
Look at the `switch-to-*` tasks if you want to see how this works.

Let's remove the init, switch, make, and make sub-tasks discussed above from the
available task list:

    * check-reuse:                Check if project is REUSE compliant.
    * clean:                      Remove virtual environments and generated files.
    * lockfiles-disable:          Disable backend to use requirements.txt files managed by pip-compile as lock files.
    * lockfiles-enable:           Enable backend to use requirements.txt files managed by pip-compile as lock files.
    * main:                       Run the __main__ module code, passing arguments to the module.  Example: task main -- --version
    * make-env:                   Create and update virtual environment
    * pypi-version:               Get the current version of the given package(s) from pypi and output as PEP508 dependency specifier(s).
    * reuse-disable:              Disable using SPDX reuse for enforcing copyright and license.
    * reuse-enable:               Enable using SPDX reuse for enforcing copyright and license.
    * reuse-lint:                 Perform reuse checks if pyproject.toml: tools.taskfile.reuse is set to "enabled"
    * test:                       Run the unit tests for the supported versions of python.

and look at pre-commit task which is invoked in .pre-commit-config.yaml when ran
by pre-commit in the build task.

    ➤ task pre-commit --summary
    task: pre-commit

    Must pass before allowing version control commit.

    commands:
     - Task: check-pyproject

The `test` task runs pytest for each of the supported python versions while the
`coverage` task uses the supported python version from the pyproject.toml file.

    ➤ task test --summary
    task: test

    Run the unit tests for the supported versions of python.

    commands:
     - Task: fe:unit-test

    ➤ task fe:unit-test --summary
    task: fe:unit-test

    (task does not have description or summary)

    commands:
     - hatch -- test --show
     - hatch -- test --all

    ➤ task coverage --summary
    task: coverage

    Run the unit tests with coverage.

    commands:
     - hatch run -- test:pytest --cov-report term-missing --cov-report json:metrics/coverage.json --cov=foobar tests

Pytest and Coverage have configuration options in `pyproject.toml`
(`tool.pytest` and `tool.coverage` tables).

Removing the `test` and `pre-commit` tasks from the available task list:

    * check-reuse:                Check if project is REUSE compliant.
    * clean:                      Remove virtual environments and generated files.
    * lockfiles-disable:          Disable backend to use requirements.txt files managed by pip-compile as lock files.
    * lockfiles-enable:           Enable backend to use requirements.txt files managed by pip-compile as lock files.
    * main:                       Run the __main__ module code, passing arguments to the module.  Example: task main -- --version
    * make-env:                   Create and update virtual environment
    * pypi-version:               Get the current version of the given package(s) from pypi and output as PEP508 dependency specifier(s).
    * reuse-disable:              Disable using SPDX reuse for enforcing copyright and license.
    * reuse-enable:               Enable using SPDX reuse for enforcing copyright and license.
    * reuse-lint:                 Perform reuse checks if pyproject.toml: tools.taskfile.reuse is set to "enabled"

The `clean` task is pretty self-evident. If you want a totally clean
environment, then running clean followed by a `switch-to-*` task or the `make`
task will do the job:

    ➤ task clean
    ➤ task switch-to-poetry

or

    ➤ task clean
    ➤ task make

or

    ➤ task clean
    ➤ task make-env
    ➤ task update-env

The `make-env` creates the virtual environment while `update-env` pip installs
your project into the virtual environment.

The reuse tasks support using the SPDX reuse system. You may enable or disable
using the system. The `reuse-lint` task is usually called by the `lint` task and
just conditionally runs "reuse lint" if reuse is enabled in the pyproject.toml
file's `tool.taskfile` table. If you do not want reuse, you might want to remove
it from the `.pre-commit-config.yaml` file.

Now we are down to

    * lockfiles-disable:          Disable backend to use requirements.txt files managed by pip-compile as lock files.
    * lockfiles-enable:           Enable backend to use requirements.txt files managed by pip-compile as lock files.
    * main:                       Run the __main__ module code, passing arguments to the module.  Example: task main -- --version
    * pypi-version:               Get the current version of the given package(s) from pypi and output as PEP508 dependency specifier(s).

`pypi-version` simply queries pypi.org for the latest version of a package:

    ➤ task pypi-version -- requests
    task: [pypi-version] scripts/latest_pypi_version.sh requests
    requests>=2.32.3

The output is a version specifier that can be copied into
`project.dependencies`. Not as nice as poetry's `add` command.

`lockfiles-*` or used by hatch and setuptools to enable/disable using
pip-compile to resolve dependencies.

And that leaves us with the main task, which is just a shortcut for running the
project in the project manager's virtual environment. Try it:

    ➤ task main -- --help

Note, you do need the "--" after the task name.

### Adding a dependency using poetry

Add the dependency using the poetry CLI.

    poetry add --group dev some_tool
    task build

The build ought to fail as [project] and [tool.poetry] dependencies are now out
of sync. But the build output includes the PEP 508 dependency just added that
you can copy and paste into the [project] table's appropriate dependency.

    task build

Should pass this time.

### Adding a dependency using hatch

Optionally run `task pypi-version` to retrieve the latest version of a package
on pypi. Ex:

    ➤ task pypi-version -- requests
    task: [pypi-version] scripts/latest_pypi_version.sh requests
    requests>=2.32.3

Note the output is a version specifier all ready to be copied into
pyproject.toml.

Manually edit the `pyproject.toml` file and add the dependency to both [project]
and [tool.poetry] dependency tables. Then running

    task build

Will show any version specifier mismatches...

### Summary

Yes, there are more tasks than I like. In real use, you usually settle on one
development system and once settled in, your workflow should be something like:

    edit
    task make
    ...
    edit
    task make
    task test

    task doc
    ...
    edit
    task doc

    git add
    git commit
    git push

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

Both poetry and hatch make use of virtual environments. For Setuptools, a
virtual environment is recommended, so we use one. To enable all development
systems to share the same virtual environment and to share the same virtual
environment with PyCharm, the project's `.venv/` virtual environment is used.

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
a `task run true` but any `task run ...` or `task shell` will do.

### src/ layout

The file structure is:

    .
    .venv/                    # virtual environment shared by: hatch, poetry, & IDE
    .reuse/                   # generated reuse templates
    dist/                     # generated distribution files
    docs/                     # documentation source files
    LICENSES/                 # license files
    metrics/                  # generated metrics reports
    node_modules              # generated by pre-commit
    scripts/                  # project build scripts
    site/                     # generated documentation
    src/                      # project source files
    tests/                    # unit test files
    .coverage                 # generated coverage database file
    .gitignore                # files not to check in to git
    .pre-commit-config-yaml   # pre-commit config file
    .python-version           # generated by pyenv list of python versions
    DEV-README.md             # this file
    mkdocs.yml                # mkdocs documentation system config file
    poetry.lock               # poetry resolved dependency lock file
    README.md                 # Standard README file in markdown format
    reuse.spdx                # generated bill of materials
    Taskfile.yml              # link to active taskfile
    Taskfile-hatch.yml        # hatch based taskfile
    Taskfile-poetry.yml       # poetry based taskfile
    tox.ini                   # tox configuration file

### testing

Pytest is used for unit testing. The test cases are in the `tests/` directory.
Configuration is in `pyproject.toml:tool.pytest.ini_options` table instead of
the traditional `pytest.ini` file.

#### tox

When using poetry, multiple python testing is via tox, with `tox.ini` being the
configuration file.

#### matrix testing

When using hatch, pytest is run on each version of python in the test matrix in
`pyproject.toml`:

    [[tool.hatch.envs.test.matrix]]
    python = ["3.11", "3.12"]

#### coverage

Code coverage is performed using the default python version to run pytest +
coverage.

### lint

I'm a big fan of letting the computer find my issues, yes I like linters. So
there are a few linters in the lint task, some of which overlap.

    ➤ task lint --summary
    task: lint

    Perform static code analysis.

    commands:
     - poetry run -- ruff check --config pyproject.toml --fix src tests
     - poetry run -- scripts/run-mypy-all-python-versions.sh
     - poetry run -- fawltydeps --detailed || true
     - poetry run -- reuse lint
     - poetry run -- pyupgrade --py311-plus
     - scripts/fail_on_regex_match.sh "PyBind|Numpy|Cmake|CCache|Github|PyTest"
     - git ls-files -z -- "*.sh" | xargs -0 poetry run -- shellcheck

Note the use of two scripts. `scripts/run-mypy-all-python-versions.sh` and
`scripts/fail_on_regex_match.sh`. Both replace or mimic pre-commit tasks.

#### run-mypy-all-python-versions.sh

The default mypy pre-commit task requires hard-coding the python version in the
`.pre-commit-config.yaml` file. So created
`scripts/run-mypy-all-python-versions.sh` script that runs mypy for each python
major.minor version in the .python-version file which is controlled by pyenv.

#### fail_on_refex_match.sh

This is a simple test that searches for some common capitalization mistakes. The
intent is to find these problems in the build task instead of in the pre-commit.

### mkdocs

The configuration file for `mkdocs` is `mkdocs.yml`. The source file is
`docs/index.md` which is just a symbolic link to the project's `README.md` file.
Also by default the project's API is documented in the **code reference**
section using the code's docstrings. The HTML output is written to `site/`
directory.

Note that `scripts/gen_ref_pages.py` supports automatic API generation and is
used in `mkdocs.yml`.

While the default documentation is simple, it should suffice for most simple
projects and is easily expandable for more complex projects.

### pre-commit

Pre-commit is one of those love/hate relationships. I like sanitizing changes
going into my repo. But really dislike commits being blocked. The solution is
for `task build` to run the pre-commit checks. So once you have a passing build,
it really ought to be committable.

The pre-commit checks are defined in `.pre-commit-config.yaml` which includes
running `task pre-commit`.

    ➤ task pre-commit --summary
    task: pre-commit

    Must pass before allowing version control commit.

    commands:
     - Task: check-pyproject
     - Task: tests

### poetry.lock

Poetry will resolve dependencies then write them into the `poetry.lock` file,
which probably should in your version control system. The purpose of the
lockfile is to ensure that exactly the same versions of all the dependencies are
installed each time.

Hatch currently does not have an equivalent feature. There is a plugin,
[hatch-pip-compile](https://juftin.com/hatch-pip-compile/) that manages project
dependencies and lockfiles. References
[Feature request: Lock file support for applications](https://github.com/pypa/hatch/issues/749#top)

### reuse

My verdict is still out on [REUSE](https://reuse.software/). I have been on
projects where legal wants all the licenses we are using. Not a fun exercise. So
REUSE aims to facilitate managing a project's licenses. The pain point is adding
a copyright/license header to every file. The sweet point is automated bill of
material reporting. Time will tell...

Until then, I made using reuse optional. I added a table and setting to the
pyproject.toml:

    ### local Taskfile.yml options (not Taskfile options)

    [tool.taskfile]
    # For reuse copyright/license checking set reuse to either "enabled" or "disabled"
    # You should not directly edit this setting.  Instead, use the tasks "task reuse-enable" and
    # "task reuse-disable" as they also update the .git/hooks/pre-commit to either skip or not
    # skip the reuse hook.
    reuse = "disabled"

and split running reuse lint from the `lint` task to a new `reuse-lint` task
dependent upon the above reuse setting. All controlled with the `reuse-enable`
and `reuse-disable` tasks

### git

Currently, this project assumes git is the vcs. There are minimal direct usages
of git, so should be easily ported to another vcs. Also have intentionally
assumed not using GitHub, so no GitHub actions.

### Build tools

- [loguru](https://loguru.readthedocs.io) improved logging.
- [pytest](https://docs.pytest.org) unit testing.
- [pathvalidate](https://pathvalidate.readthedocs.io)
- [tox](https://tox.wiki) multiple python testing.
- [radon](https://radon.readthedocs.io) code metrics.
- [Ruff](https://docs.astral.sh/ruff/) is an extremely fast Python linter and
  code formatter, written in Rust.
- [FawltyDeps](https://github.com/tweag/FawltyDeps) is a dependency checker for
  Python that finds undeclared and/or unused 3rd-party dependencies in your
  Python project.
- [Reuse](https://reuse.readthedocs.io/) is a tool for compliance with the
  [REUSE](https://reuse.software/) recommendations.
- [MyPy](https://www.mypy-lang.org/)

#### FawltyDeps

This tool does a great job in helping keep bloat out of your project. There is
one small issue with it, it does not distinguish project dependencies from
dev/test/doc/... dependencies. So you have to manually add any new tools to the
used list in your [pyproject.toml], like:

    [tool.fawltydeps]
    code = ["src"]  # Only search for imports under ./src
    deps = ["pyproject.toml"]  # Only look for declared dependencies here
    ignore_unused = ["radon", "pytest-cov", "pytest", "tox", "fawltydeps", "mkdocs", "mkdocstrings-python",
      "mkdocs-literate-nav", "mkdocs-section-index", "ruff", "mkdocs-material", "mkdocs-gen-files",]

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

## CLIBones

CLIBones is a command line interface (CLI) application skeleton (Bones). The
main intent is to provide argument and config file handling with hardly any
effort, so it encapsulates argparse, ConfigParser in a `Settings` context
manager. Note that `Settings` uses argparse, giving you the power to have really
nice arguments (sorry, couldn't resist). This makes your main function look
something like:

    def main(args: list[str] | None = None) -> int:
        """The command line applications main function."""
        exit_code: int = 0
        with Settings(args=args) as settings:
            # some info commands (--version, --longhelp) need to exit immediately
            # after completion.  The quick_exit flag indicates if this is the case.
            if settings.quick_exit:
                return 0

            # TODO: Here be dragons!  In other words, your app goes here.
            exit_code = MyApp.run(settings)

        return exit_code

Please look in the `{app_package}/__main__.py` for more details on adding
argument options and parsers. And to complete the earlier forward reference,
`ApplicationSettings` is the parent class to `Settings` and contains the
argument parsing.

The CLIBones files are located in `{app_package}/clibones` package.

Feel free to rip clibones out and roll your own bones. ;-)

### Architecture

The architecture used is a Settings context manager that handles all the command
line and config file argument definition, parsing, and validation.

The application's entry point is in `{app_package}/__main__.py`. In
`__main.py__` there are several TODOs that you will need to visit and clear.

The application may be run with any of the following:

- `python3 -m {app_package} --help`
- `poetry run python3 -m {app_package} --help`
- `task main --help`

So in general, for each command line argument you ought to:

- optionally add an argument group to the parser in `Settings.add_arguments()`
- add argument to the parser in `Settings.add_arguments()`
- optionally add validation to `Settings.validate_arguments()`

Refer to `application_settings.py` which implements help and logging as
examples.

The `__example_application()` demonstrates using a `GracefulInterruptHandler` to
capture ^C for a main loop.

Next take a look at `main.main()` which demonstrates the use of the Settings
context manager.

The `Settings` does have a few extra features including:

- config files are supported for any command arguments you want to persist.
- standard logging setup via command line arguments.
