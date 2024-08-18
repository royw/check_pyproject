# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

"""
main entry point for application that checks pyproject.toml for consistency between project and tool.poetry tables.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from check_pyproject.check_pyproject_toml import validate_pyproject_toml_file
from check_pyproject.settings import Settings


def main(args: list[str] | None = None) -> int:
    """The command line applications main function."""
    number_of_problems: int = 0
    with Settings(args=args) as settings:
        # some info commands (--version, --longhelp) need to exit immediately
        # after completion.  The quick_exit flag indicates if this is the case.
        if settings.quick_exit:
            return 0
        # process each pyproject.toml file passed on the commandline.
        for arg in settings.pyproject_toml_files:
            logger.info(f'Checking: "{arg}"')
            number_of_problems += validate_pyproject_toml_file(Path(arg))
    return number_of_problems


if __name__ == "__main__":
    sys.exit(main(args=None))  # pragma: no cover
