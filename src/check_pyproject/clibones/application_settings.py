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

import argparse
import contextlib
import os
import sys
from abc import ABC, abstractmethod
from collections.abc import Sequence
from configparser import ConfigParser, NoSectionError

from check_pyproject.clibones.info_control import InfoControl
from check_pyproject.clibones.logger_control import LoggerControl


class ApplicationSettings(ABC):
    """
    Usage::

        class MySettings(ApplicationSettings):
            HELP = {
                "foo": "the foo option",
                "bar": "the bar option",
            }

            def __init__(self):
                super(MySettings, self).__init__(
                    "App Name", "app_package", "app_description", ["APP Section"]
                )

            def add_arguments(parser):
                parser.add_argument("--foo", action="store_true", help=HELP["foo"])
                parser.add_argument("--bar", action="store_true", help=HELP["bar"])

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
        config_files: list[str] | None = None,
        args: Sequence[str] | None = None,
    ) -> None:
        """
        :param str app_name: The application name
        :param app_package: The application's package name
        :param config_sections: The INI sections in the config file to import in as defaults to the argument parser.
        :param config_files: A list of config files to load
        :param args: A list of arguments to pass to the application.  If none then get arguments from sys.argv
        """
        self.__app_name: str = app_name
        self.__app_package: str = app_package
        self.__app_description = app_description
        self.__config_sections: list[str] = config_sections
        self.__config_files: list[str] = config_files or []
        self.__args: Sequence[str] = args or sys.argv[1:]
        self._parser: argparse.ArgumentParser | None = None
        self._settings: argparse.Namespace | None = None
        self._remaining_argv: list[str] = []
        self.quick_exit: bool = False
        self.logger_control = LoggerControl()
        self.info_control = InfoControl(app_package=app_package)

    def _parse_config_files(
        self, args: Sequence[str] | None = None
    ) -> tuple[
        argparse.ArgumentParser | None,
        list[str],
        dict,
        list[str],
    ]:
        config_parser_help = f"Configuration file in INI format (default: {self._default_config_files()})"
        conf_parser: argparse.ArgumentParser = argparse.ArgumentParser(add_help=False)
        conf_parser.add_argument("--config", metavar="FILE", help=config_parser_help)

        parse_args, remaining_argv = conf_parser.parse_known_args(args=args)

        config_files = self.__config_files or self._default_config_files()[:]
        if parse_args.config:
            config_files.insert(0, parse_args.config)

        config = ConfigParser()
        config.read(config_files)
        defaults = {}
        for section in self.__config_sections:
            with contextlib.suppress(NoSectionError):
                defaults.update(dict(config.items(section)))

        return conf_parser, config_files, defaults, remaining_argv

    def parse(
        self, args: Sequence[str] | None = None
    ) -> tuple[argparse.ArgumentParser, argparse.Namespace, list[str]]:
        """
        Perform the parsing of the optional config files and the command line arguments.

        return: the parser and the settings
        """

        # parse any config files
        conf_parser, config_files, defaults, remaining_argv = self._parse_config_files(args=args)
        parent_parsers: Sequence = [conf_parser, *self.add_parent_parsers()]

        parser = argparse.ArgumentParser(self.__app_name, parents=parent_parsers, description=self.__app_description)

        if defaults:
            parser.set_defaults(**defaults)

        self.info_control.add_arguments(parser=parser)
        self.logger_control.add_arguments(parser=parser)

        self.add_arguments(parser, defaults)

        settings, leftover_argv = parser.parse_known_args(args=remaining_argv)
        # copy quick_exit into namespace for context usage
        setattr(settings, "quick_exit", self.quick_exit)
        settings.config_files = config_files

        return parser, settings, leftover_argv

    def _default_config_files(self) -> list[str]:
        """
        Defines the default set of config files to try to use.  The set is:
        * ".appnamerc" in the current directory
        * "~/.appname/{appname}.conf"

        You may override this method if you want to use a different set of config files.

        :return: the set of config file locations
        """
        rc_name: str = f".{self.__app_package}rc"
        conf_name: str = os.path.expanduser(f"~/.local/{self.__app_package}.conf")
        return [rc_name, conf_name]

    @abstractmethod
    def add_parent_parsers(self) -> list[argparse.ArgumentParser]:
        """
        This is where you should add any parent parsers for the main parser.

        :return: a list of parent parsers
        """
        return []

    @abstractmethod
    def add_arguments(self, parser: argparse.ArgumentParser, defaults: dict[str, str]) -> None:
        """
        This is where you should add arguments to the parser.

        To add application arguments, you should override this method.

        :param parser: the argument parser with --config already added.
        :param defaults: the default dictionary usually loaded from a config file
        """
        return

    @abstractmethod
    def validate_arguments(self, settings: argparse.Namespace, remaining_argv: list[str]) -> list[str]:
        """
        This provides a hook for validating the settings after the parsing is completed.

        :param settings: the settings object returned by ArgumentParser.parse_args()
        :param remaining_argv: the remaining argv after the parsing is completed.
        :return: a list of error messages or an empty list
        """

        return []

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

    def __exit__(self, exc_type, exc_val, exc_tb):
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
