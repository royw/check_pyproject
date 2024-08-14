# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import contextlib
from collections.abc import Generator
from pathlib import Path
from typing import Any

import tomlkit
from _pytest.capture import CaptureFixture

import check_pyproject
from check_pyproject.__main__ import main

"""
This is a sanity check to make sure versions are working as expected.
Yes, we have two definitive sources of version, both in pyproject.toml,
one for poetry (tool.poetry.version), and one for everyone else
(project.version).
Then for our project, we extract the version from the metadata, which
should have been generated from the current pyproject.toml file.
Thus, let's be sure this pythonisque SNAFU is actually working...
"""


@contextlib.contextmanager
def pyproject() -> Generator[dict[str, Any], None, None]:
    path = Path(__file__).parent.parent / "pyproject.toml"
    with path.open() as fp:
        yield tomlkit.loads(fp.read()).value


def test_project_and_poetry_versions_are_in_sync() -> None:
    """Checks if project.version and tool.poetry.version in pyproject.toml are in sync"""

    with pyproject() as data:
        assert data["project"]["version"] == data["tool"]["poetry"]["version"]


def test_poetry_versions_are_in_sync() -> None:
    """Checks if the pyproject.toml:tool.poetry.version and package.__init__.py __version__ are in sync."""

    with pyproject() as data:
        assert check_pyproject.__version__ == data["tool"]["poetry"]["version"]


def test_project_versions_are_in_sync() -> None:
    """Checks if the pyproject.toml:project.version and package.__init__.py __version__ are in sync."""

    with pyproject() as data:
        assert check_pyproject.__version__ == data["project"]["version"]


def test_cli_versions_are_in_sync(capsys: CaptureFixture[Any]) -> None:
    """Checks if the CLI --version output is in sync with pyproject.toml."""

    with pyproject() as data:
        assert main(["--version"]) == 0
        captured = capsys.readouterr()
        assert data["project"]["version"] in captured.out
