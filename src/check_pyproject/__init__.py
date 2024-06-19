# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

"""# Check PyProject

Check that [project] and [tool.poetry] tables are in-sync in the `pyproject.toml` file.

The Python Packaging User Guide now specifies `pyproject.toml` metadata.

Poetry <2.0 predates the metadata specification and instead used the then current standard of
[tool.poetry] table.  While there is a lot of overlap, there are some differences (ex. dependency package specifiers).
Poetry 2.0 will support PyPA pyproject.toml specification (formerly PEP 621) which will obsolete
this utility.

So if your project uses poetry and any other tool that requires the current pyproject.toml metadata, or you
are prepping for Poetry 2.0 and do not want to use the development version of Poetry.
then you need to manually maintain sync between [project] and [tool.poetry] tables.

This tool checks that overlapping metadata, between [project] and [tool.poetry] tables, is roughly in-sync.
"""
