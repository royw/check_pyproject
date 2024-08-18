from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from pathvalidate.argparse import validate_filepath_arg

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
            config_sections=[Settings.__project_package],
            args=args,
        )
        self.add_persist_keys({"pyproject_toml_files", "loglevel", "debug"})

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
            help="The pyproject.toml file(s) to check",
        )

    def validate_arguments(self, settings: argparse.Namespace, remaining_argv: list[str]) -> list[str]:  # noqa: ARG002
        """This provides a hook for validating the settings after the parsing is completed.

        :param settings: the settings object returned by ArgumentParser.parse_args()
        :param remaining_argv: the remaining argv after the parsing is completed.
        :return: a list of error messages or an empty list
        """
        return []
