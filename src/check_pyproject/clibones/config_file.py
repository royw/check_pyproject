# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Callable
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import tomlkit.parser

from check_pyproject.clibones.config_file_base import ConfigFileBase

# ================================================================================
# Add import of format specific config file then add to SUPPORTED_FORMATS list
from check_pyproject.clibones.json_config_file import JsonConfigFile
from check_pyproject.clibones.toml_config_file import TomlConfigFile

SUPPORTED_FORMATS: list[type[ConfigFileBase]] = [TomlConfigFile, JsonConfigFile]
# ================================================================================


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
