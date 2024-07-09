# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

"""
A context manager base class that optionally reads a config file then uses the values as defaults
for command line argument parsing.

To be useful, you must derive a class from this base class, and you should override at least the **add_arguments**
method.  You may find it useful to also override **_default_config_files** and **arguments_validate** methods.

This base class adds the following features to ArgumentParser:

* config file support from either the command line (--config FILE) or from expected locations (current
  directory then user's home directory).  The default config file name is created by prepending '.' and appending
  'rc' to the applications package name (example, app_package = 'foobar', then config file name would be
  '.local/foobar.conf' or '.foobarrc' and the search order would be: ['./.foobarrc', '~/.local/foobar.conf']).

* display the application's --version from app_package.version (usually defined in app_package/__init__.py).

* display the application's --longhelp which is the module docstring in app_package/__init__.py.

* initializing the root logging using --verbosity LEVEL, --quiet, --debug, and --logfile FILENAME

"""

from __future__ import annotations

import argparse
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from check_pyproject.clibones.config_file import ConfigFile
from check_pyproject.clibones.info_control import InfoControl
from check_pyproject.clibones.logger_control import LoggerControl

if TYPE_CHECKING:
    from collections.abc import Sequence


class ApplicationSettings(ABC):
    """
    Usage::

        class MySettings(ApplicationSettings):
            def __init__(self):
                super(MySettings, self).__init__("App Name", "app_package", "app_description", ["APP Section"])

            def add_arguments(parser):
                parser.add_argument("--foo", action="store_true", help="It's all about foo")
                parser.add_argument("--bar", action="store_true", help="Just the best, bar none")

    Context Manager Usage::

        with MySettings() as settings:
            if settings.foo:
                pass

    Traditional Usage::

        parser, settings = MySettings().parse()
        if settings.foo:
            pass
    """

    def __init__(
        self,
        app_name: str,
        app_package: str,
        app_description: str,
        config_sections: list[str],
        default_config_file: Path | None = None,
        args: Sequence[str] | None = None,
    ) -> None:
        """
        :param str app_name: The application name
        :param app_package: The application's package name
        :param default_config_file: The default config file to load, None means no default config file.
        :param args: A list of arguments to pass to the application.  If none then get arguments from sys.argv
        """
        self.__app_name: str = app_name
        self.__app_package: str = app_package
        self.__app_description = app_description
        self.__config_sections: list[str] = config_sections
        self.__default_config_file: Path | None = default_config_file
        self.__args: Sequence[str] = args or sys.argv[1:]

        self._parser: argparse.ArgumentParser | None = None
        self._settings: argparse.Namespace | None = None
        self._remaining_argv: list[str] = []
        self._persist_keys: set[str] = set()
        self.quick_exit: bool = False
        self.logger_control = LoggerControl()
        self.info_control = InfoControl(app_package=app_package)

        if self.__default_config_file is None:
            self.__default_config_file = Path.home() / ".config" / f"{self.__app_package}.toml"

    @abstractmethod
    def add_parent_parsers(self) -> list[argparse.ArgumentParser]:  # pragma: no cover
        """
        This is where you should add any parent parsers for the main parser.

        :return: a list of parent parsers
        """
        return []

    @abstractmethod
    def add_arguments(self, parser: argparse.ArgumentParser, defaults: dict[str, str]) -> None:  # pragma: no cover
        """
        This is where you should add arguments to the parser.

        To add application arguments, you should override this method.

        :param parser: the argument parser with --config already added.
        :param defaults: the default dictionary usually loaded from a config file
        """
        return

    @abstractmethod
    def validate_arguments(
        self, settings: argparse.Namespace, remaining_argv: list[str]
    ) -> list[str]:  # pragma: no cover
        """
        This provides a hook for validating the settings after the parsing is completed.

        :param settings: the settings object returned by ArgumentParser.parse_args()
        :param remaining_argv: the remaining argv after the parsing is completed.
        :return: a list of error messages or an empty list
        """
        return []

    def add_persist_keys(self, keys: set[str]) -> None:
        self._persist_keys |= keys

    def parse(self, args: Sequence[str]) -> tuple[argparse.ArgumentParser, argparse.Namespace, list[str]]:
        """
        Perform the parsing of the optional config files and the command line arguments.

        return: the parser, the settings, and any remaining arguments.
        """
        config_file = ConfigFile()
        config_file.default_config_file = self.__default_config_file
        config_file.section_name = self.__app_package
        config_file.persist_keys = self._persist_keys
        dash_config_parser, remaining_args, defaults = config_file.parser(args=args)

        parser = argparse.ArgumentParser(
            self.__app_name,
            parents=[dash_config_parser, *self.add_parent_parsers()],
            description=self.__app_description,
        )

        # add arguments to the parser
        self.info_control.add_arguments(parser=parser)
        self.logger_control.add_arguments(parser=parser)
        self.add_arguments(parser=parser, defaults=defaults or {})

        if defaults:
            parser.set_defaults(**defaults)

        # drum roll... Perform the parse!
        settings, leftover_args = parser.parse_known_args(args=remaining_args)

        # copy quick_exit into namespace for context usage
        settings.quick_exit = self.quick_exit
        settings.config_file = config_file.config_filepath

        config_file.save_config_file(vars(settings))

        return parser, settings, leftover_args

    def __enter__(self) -> argparse.Namespace:
        """context manager enter
        :return: the settings namespace
        """
        self._parser, self._settings, self._remaining_argv = self.parse(args=self.__args)

        self.logger_control.setup(self._settings)
        self.info_control.setup(self._settings)

        if not self._settings.quick_exit:
            # validate both the base ApplicationSettings.validate_arguments and the child's validate_arguments.
            # combine the results which each can be either a list of error message strings or an empty list
            error_messages: list[str] = ApplicationSettings.validate_arguments(
                self, self._settings, self._remaining_argv
            ) + self.validate_arguments(self._settings, self._remaining_argv)

            for error_msg in error_messages:
                self._parser.error(error_msg)

            self._settings.parser = self._parser
        return self._settings

    def __exit__(self, *exc: Any) -> None:  # NOQA: B027
        """
        context manager exit
        """

    def help(self) -> int:
        """
        Let the parser print the help message.

        :return: 2
        """
        if self._parser:
            self._parser.print_help()
        return 2
