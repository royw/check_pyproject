# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import tomlkit

from check_pyproject.clibones.config_file_base import ConfigFileBase


class TomlConfigFile(ConfigFileBase):
    @staticmethod
    def register(config_file: Any) -> None:
        config_file.register(".toml", TomlConfigFile.load, TomlConfigFile.save)
        config_file.register(".tml", TomlConfigFile.load, TomlConfigFile.save)

    @staticmethod
    def load(filepath: Path) -> dict[str, Any]:
        with filepath.open(encoding="utf-8") as f:
            data: dict[str, Any] = tomlkit.load(f).value
            return data

    @staticmethod
    def save(filepath: Path, config_dict: dict[str, Any]) -> None:
        # write to temporary file then atomically "switch" it with the original using rename.
        with tempfile.NamedTemporaryFile("wt", dir=filepath.parent, delete=False) as tf:
            tf.write(tomlkit.dumps(config_dict))
            temp_name = Path(tf.name)
        temp_name.rename(filepath)
