# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from check_pyproject.clibones.config_file_base import ConfigFileBase


class JsonConfigFile(ConfigFileBase):
    @staticmethod
    def register(config_file: Any) -> None:
        config_file.register(".json", JsonConfigFile.load, JsonConfigFile.save)

    @staticmethod
    def load(filepath: Path) -> dict[str, Any]:
        with filepath.open(encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            errmsg = f'Data loaded from "{filepath}" is not a dictionary.'
            raise ValueError(errmsg)

    @staticmethod
    def save(filepath: Path, config_dict: dict[str, Any]) -> None:
        # write to temporary file then atomically "switch" it with the original using rename.
        with tempfile.NamedTemporaryFile("wt", dir=filepath.parent, delete=False) as tf:
            tf.write(json.dumps(config_dict))
            temp_name = Path(tf.name)
        temp_name.rename(filepath)
