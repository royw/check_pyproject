# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ConfigFileBase(ABC):
    @staticmethod
    @abstractmethod
    def register(config_file: Any) -> None:
        pass

    @staticmethod
    @abstractmethod
    def load(filepath: Path) -> dict[str, Any]:
        pass

    @staticmethod
    @abstractmethod
    def save(filepath: Path, config_dict: dict[str, Any]) -> None:
        pass
