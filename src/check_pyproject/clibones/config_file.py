# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import TYPE_CHECKING, Any

import tomlkit.parser

from check_pyproject.clibones.config_file_base import ConfigFileBase

if TYPE_CHECKING:
    from collections.abc import Sequence

# ================================================================================
# Add import of format specific config file then add to SUPPORTED_FORMATS list
from check_pyproject.clibones.json_config_file import JsonConfigFile
from check_pyproject.clibones.toml_config_file import TomlConfigFile

SUPPORTED_FORMATS: list[type[ConfigFileBase]] = [TomlConfigFile, JsonConfigFile]
# ================================================================================


@dataclass
class ConfigFile:
    """
    Reading and writing config files of multiple file formats.
    Converts any exceptions in load or save to ValueError.

    Usage:

        config_file = ConfigFile()
        config_data = config_file.load(f"{app_name}.toml")
        with Settings() as settings:
            config_file.save(f"{app_name}.toml", settings)
    """

    persist_keys: set[str] | None = None
    section_name: str | None = None
    default_config_file: Path | None = None
    config_filepath: Path | None = None
    save_config_filepath: Path | None = None

    def __init__(self) -> None:
        self.registered_formats: dict[
            str, tuple[Callable[[Path], dict[str, Any]], Callable[[Path, dict[str, Any]], None]]
        ] = {}
        self.supported_formats: list[type[ConfigFileBase]] = SUPPORTED_FORMATS
        for supported_format in self.supported_formats:
            supported_format.register(self)

    def register(
        self, extension: str, loader: Callable[[Path], dict[str, Any]], saver: Callable[[Path, dict[str, Any]], None]
    ) -> None:
        """register an extension with loader and saver methods."""
        self.registered_formats[extension] = (loader, saver)

    @property
    def supported_extensions(self) -> list[str]:
        """return the list of supported extensions. Note the extension includes the leading dot (ex: ".toml")"""
        return list(self.registered_formats.keys())

    def load(self, filepath: Path | None) -> dict[str, Any]:
        """
        load config file return a dictionary with the loaded data.

        raises: ValueError
        """
        if filepath is None:
            return {}

        try:
            return self.registered_formats[filepath.suffix][0](filepath)
        except ValueError as ex:
            raise ex
        except KeyError as ex:
            errmsg = f"No config file loader found for {filepath}"
            raise ValueError(errmsg) from ex
        except (JSONDecodeError, tomlkit.parser.ParseError, TypeError) as ex:
            errmsg = f"The config file ({filepath}) could not be loaded: {ex}"
            raise ValueError(errmsg) from ex

    def save(self, filepath: Path, config_dict: dict[str, Any]) -> None:
        """
        save config file given a dictionary with the data to save.

        raises: ValueError
        """
        if not isinstance(config_dict, dict):
            errmsg = f"The config file ({filepath}) must be a dictionary"  # type: ignore[unreachable]
            raise ValueError(errmsg)
        try:
            self.registered_formats[filepath.suffix][1](filepath, config_dict)
        except ValueError as ex:
            raise ex
        except KeyError as ex:
            errmsg = f"No config file saver found for {filepath}"
            raise ValueError(errmsg) from ex
        except (JSONDecodeError, tomlkit.parser.ParseError, TypeError) as ex:
            errmsg = f"Cannot convert the data to the format of the config file {filepath}: {ex}"
            raise ValueError(errmsg) from ex

    def parser(self, args: Sequence[str]) -> tuple[argparse.ArgumentParser, Sequence[str], dict[str, Any] | None]:
        config_parser_help = f"Configuration file (default: {self.default_config_file})"
        dash_config_parser: argparse.ArgumentParser = argparse.ArgumentParser(add_help=False)
        dash_config_parser.add_argument("--config", metavar="FILE", help=config_parser_help)
        dash_config_parser.add_argument(
            "--save-config", dest="save_config", action="store_true", help=config_parser_help
        )
        dash_config_parser.add_argument("--save-config-as", metavar="FILE", help=config_parser_help)
        parse_args, remaining_args = dash_config_parser.parse_known_args(args=args)

        # desired config files may also be located in self.__config_files and in self._default_config_files(),
        # so combine the three possible sources with the "--config FILE" being first in the list.
        self.config_filepath = self.default_config_file
        if parse_args.config:
            self.config_filepath = Path(parse_args.config)
        if parse_args.save_config:
            self.save_config_filepath = self.config_filepath
        if parse_args.save_config_as:
            self.save_config_filepath = Path(parse_args.save_config_as)

        defaults: dict[str, Any] = {}
        if self.config_filepath is not None:
            try:
                data = self.load(self.config_filepath)
                if self.section_name in data:
                    defaults = self.filter_keys(data[self.section_name], self.persist_keys or set(), defaults)
            except FileNotFoundError:
                # the config file doesn't exist, which is ok and means no defaults...
                pass
        return dash_config_parser, remaining_args, defaults

    @staticmethod
    def filter_keys(data: dict[str, Any], persist_keys: set[str], filtered_data: dict[str, Any]) -> dict[str, Any]:
        for key in data:
            if key in persist_keys:
                filtered_data[key] = data[key]
        return filtered_data

    def save_config_file(self, settings: dict[str, Any]) -> None:
        data = {}
        if self.save_config_filepath:
            if self.persist_keys:
                for key in self.persist_keys:
                    if key in settings:
                        data[key] = settings[key]

            self.save(
                filepath=self.save_config_filepath, config_dict={self.section_name or "missing section_name": data}
            )
