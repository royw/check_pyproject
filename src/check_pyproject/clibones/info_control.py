import argparse
import importlib
from argparse import ArgumentParser
from dataclasses import dataclass

from loguru import logger


@dataclass
class InfoControl:
    """Add information control (--version, --longhelp) argument support to a CLI application."""

    DEFAULT_VERSION: str = "Unknown"

    app_package: str | None = None

    # noinspection PyMethodMayBeStatic
    def add_arguments(self, parser: ArgumentParser) -> ArgumentParser:
        """Use argparse commands to add arguments to the given parser."""
        info_group = parser.add_argument_group(title="Informational Commands", description="")

        info_group.add_argument(
            "-v",
            "--version",
            dest="version",
            action="store_true",
            help="Show the application's version.  (default: %(default)s)",
        )

        info_group.add_argument(
            "--longhelp",
            dest="longhelp",
            action="store_true",
            help="Verbose help message.  (default: %(default)s)",
        )
        return parser

    def setup(self, settings: argparse.Namespace) -> None:
        """Set up the given settings.  In this case, handle the --version and --longhelp options."""
        if settings.longhelp and self.app_package:
            app_module = importlib.import_module(self.app_package)
            if app_module.__doc__:
                logger.info(app_module.__doc__)
            settings.quick_exit = True

        if settings.version and not settings.quick_exit:
            logger.info(f"Version {self._load_version()}")
            settings.quick_exit = True

    def _load_version(self) -> str:
        r"""
        Get the version from the application package's __version__ attribute.
        If not found then return DEFAULT_VERSION

        :return: the version string or DEFAULT_VERSION
        """
        try:
            if self.app_package:
                return __import__(self.app_package).version
        except (ImportError, AttributeError):
            logger.info(f"Could not import {self.app_package}.version")
        return InfoControl.DEFAULT_VERSION
