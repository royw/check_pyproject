# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

"""# Check PyProject

Checks that [project] and [tool.poetry] tables are in-sync in the `pyproject.toml` file.

The Python Packaging User Guide now specifies `pyproject.toml` metadata.

Poetry <2.0 predates the metadata specification and instead used the then current standard of
[tool.poetry] table.  While there is a lot of overlap, there are some differences (ex. dependency package specifiers).
Poetry 2.0 will support PyPA pyproject.toml specification (formerly PEP 621) which will obsolete
this utility.

So if your project uses poetry and any other tool that requires the current pyproject.toml metadata, or you
are prepping for Poetry 2.0 and do not want to use the development version of Poetry.
then you need to manually maintain sync between [project] and [tool.poetry] tables.

This tool checks that overlapping metadata, between [project] and [tool.poetry] tables, are roughly in-sync.
"""

from __future__ import annotations

from importlib import metadata
from pathlib import Path

import tomlkit

try:
    # this assumes running in an installed package
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    # this should only ever happen in the development environment,
    # so ok to assume location of pyproject.toml file.
    # Also assume src/package file layout and this file is in src/package
    # and pyproject is in the parent directory of src
    # ../../pyproject.toml
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with pyproject_path.open() as fp:
        data = tomlkit.loads(fp.read()).value
        __version__ = data["tool"]["poetry"]["version"] + "dev"
