# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from loguru import logger
from pathvalidate.argparse import validate_filepath_arg

if TYPE_CHECKING:
    from argparse import ArgumentParser


# Default loguru format for colorized output
LOGURU_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
# removed the timestamp from the logs
LOGURU_MEDIUM_FORMAT = "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
# just the colorized message in the logs
LOGURU_SHORT_FORMAT = "<level>{message}</level>"


class LoggerControl:
    """Add logger control arguments (--loglevel, --debug, --quiet, --logfile) to CLI application."""

    VALID_LOG_LEVELS: Sequence[str] = (
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    )  # cannot select NOTSET

    # noinspection PyMethodMayBeStatic
    def add_arguments(self, parser: ArgumentParser) -> None:
        """Use argparse commands to add arguments to the given parser."""

        output_group = parser.add_argument_group(title="Logging Options", description="output_group")

        output_group.add_argument(
            "--loglevel",
            dest="loglevel",
            default="INFO",
            choices=LoggerControl.VALID_LOG_LEVELS,
            help=f'Set verbosity level to one of the following: {LoggerControl.VALID_LOG_LEVELS} (default: "INFO").',
        )

        output_group.add_argument(
            "--debug",
            dest="debug",
            action="store_true",
            help="Output all messages (debug, info, warning, error, & critical).  " 'Overrides "--loglevel".',
        )

        output_group.add_argument(
            "--quiet",
            dest="quiet",
            action="store_true",
            help='Only output error and critical messages.  Overrides "--loglevel" ' 'and "--debug".',
        )

        output_group.add_argument(
            "--logfile",
            dest="logfile",
            action="store",
            type=validate_filepath_arg,
            help='File to log messages enabled by "--loglevel" to.',
        )

    @staticmethod
    def setup(settings: argparse.Namespace) -> None:
        level = "INFO"
        error_messages = []

        # convert settings to dictionary, so we can test if argument was passed
        settings_dict: dict[str, Any] = vars(settings)

        # the order of the loglevel processing is important.
        # --quiet has the highest priority followed by --debug then --loglevel
        if "loglevel" in settings_dict:
            level = settings_dict["loglevel"]
            if level not in LoggerControl.VALID_LOG_LEVELS:
                error_messages.append(
                    f"Invalid log level {level}, " f"should be one of the following: {LoggerControl.VALID_LOG_LEVELS}"
                )
                level = "INFO"

        if settings_dict.get("debug"):
            level = "DEBUG"

        if settings_dict.get("quiet"):
            level = "ERROR"

        settings.loglevel = level
        logger.remove(None)
        logger.add(sys.stdout, level=settings.loglevel, format=LOGURU_SHORT_FORMAT)

        if settings_dict.get("logfile"):
            filename = settings_dict["logfile"]
            try:
                logger.add(filename, level=settings.loglevel)
            except OSError as ex:
                error_messages += [f"Could not open logfile ({filename}): {ex}"]

        for msg in error_messages:
            logger.error(msg)
