# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

"""main entry point for application"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from pathvalidate.argparse import validate_filepath_arg

from check_pyproject.check_pyproject_toml import validate_pyproject_toml_file
from check_pyproject.clibones.application_settings import ApplicationSettings

if TYPE_CHECKING:
    import argparse
    from collections.abc import Sequence


class Settings(ApplicationSettings):
    """Where the project's initial state (i.e. settings) are defined.

    Settings extends the generic ApplicationSettings class which parses the command line arguments.

    Usage::

        with Settings() as settings:
        try:
            app.execute(settings)
            exit(0)
        except ArgumentError as ex:
            error(str(ex))
            exit(1)
    """

    __project_name: str = "Check Pyproject"
    """The name of the project"""

    __project_package: str = "check_pyproject"
    """The name of the package this settings belongs to. """

    __project_description: str = (
        f"{__project_name} checks that overlapping metadata, between [project] "
        f" and [tool.poetry] tables, is roughly) in-sync."
    )
    """A short description of the application."""

    def __init__(self, args: Sequence[str] | None = None) -> None:
        """Initialize the base class."""

        super().__init__(
            app_name=Settings.__project_name,
            app_package=Settings.__project_package,
            app_description=Settings.__project_description,
            config_sections=[Settings.__project_name],
            args=args,
        )

    def add_parent_parsers(self) -> list[argparse.ArgumentParser]:
        """This is where you should add any parent parsers for the main parser.

        :return: a list of parent parsers
        """
        return []

    def add_arguments(self, parser: argparse.ArgumentParser, defaults: dict[str, str]) -> None:  # noqa: ARG002
        """This is where you should add arguments to the parser.

        To add application arguments, you should override this method.

        :param parser: the argument parser with --conf_file already added.
        :param defaults: the default dictionary usually loaded from a config file
        """
        # use normal argparse commands to add arguments to the given parser.  Example:
        app_group = parser.add_argument_group("pyproject.toml files")
        app_group.add_argument(
            "pyproject_toml_files",
            type=validate_filepath_arg,
            nargs="*",
            default=["pyproject.toml"],
            help="The pyproject.toml files to check",
        )

    def validate_arguments(self, settings: argparse.Namespace, remaining_argv: list[str]) -> list[str]:  # noqa: ARG002
        """This provides a hook for validating the settings after the parsing is completed.

        :param settings: the settings object returned by ArgumentParser.parse_args()
        :param remaining_argv: the remaining argv after the parsing is completed.
        :return: a list of error messages or an empty list
        """
        return []


def main(args: list[str] | None = None) -> int:
    """The command line applications main function."""
    number_of_problems: int = 0
    with Settings(args=args) as settings:
        # some info commands (--version, --longhelp) need to exit immediately
        # after completion.  The quick_exit flag indicates if this is the case.
        if settings.quick_exit:
            return 0
        # If 1 or more arguments are given, they will be passed to `validate_pyproject_toml_file`.
        # Else, `validate_pyproject_toml_file` will be called with `$CWD/pyproject.toml`.
        for arg in settings.pyproject_toml_files:
            logger.info(f'Checking: "{arg}"')
            number_of_problems += validate_pyproject_toml_file(Path(arg))
    return number_of_problems


if __name__ == "__main__":
    sys.exit(main(args=None))  # pragma: no cover
