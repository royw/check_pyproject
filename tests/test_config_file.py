# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import random
import tempfile
from pathlib import Path

import pytest

from check_pyproject.clibones.config_file import ConfigFile

# dummy test data, making sure to have a dict in a dict
data = {
    "Section1": {
        "field1": "value1",
        "field2": "",  # empty strings are OK
        "field3": "value3",
    },
    "Section2": {  # empty dicts are OK
    },
}


def test_config_file_save_load() -> None:
    """round trips a known set of data by saving it, then verifying it is the same when loaded."""
    config_file = ConfigFile()
    for extension in config_file.supported_extensions:
        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / f"test_data{extension}"
            print(f"\nSaving {filepath}")
            config_file.save(filepath=filepath, config_dict=data)
            print(f"Loading {filepath}")
            config_dict = config_file.load(filepath=filepath)
            assert data == config_dict


def test_invalid_config_file_load() -> None:
    """
    Try loading an invalid config file (just a text file with random words) to verify a ValueError is raised.
    """
    config_file = ConfigFile()
    for extension in config_file.supported_extensions:
        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / f"test_data{extension}"
            with filepath.open("w") as out_fp, Path("/usr/share/dict/words").open("r") as words_fp:
                words = words_fp.read().splitlines()
                for _ in range(256):
                    out_fp.write(f"{random.choice(words)} ")

            with pytest.raises(ValueError):  # NOQA: PT011
                config_file.load(filepath=filepath)


def test_invalid_config_file_save() -> None:
    """
    Try saving an invalid config data to verify a ValueError is raised.
    """
    config_file = ConfigFile()
    for extension in config_file.supported_extensions:
        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / f"test_data{extension}"
            with pytest.raises(ValueError):  # NOQA: PT011
                # intentionally using wrong type of data to force ValueError
                # noinspection PyTypeChecker
                config_file.save(filepath=filepath, config_dict="not a dict")  # type: ignore[arg-type]


def test_unsupported_config_file_format_save() -> None:
    """test saving with an unsupported config file extension."""
    config_file = ConfigFile()
    with pytest.raises(ValueError), tempfile.TemporaryDirectory() as tmp:  # NOQA: PT011
        config_file.save(filepath=Path(tmp) / "test_data.unsupported", config_dict=data)


def test_unsupported_config_file_format_load() -> None:
    """test loading with an unsupported config file extension."""
    config_file = ConfigFile()

    with pytest.raises(ValueError), tempfile.TemporaryDirectory() as tmp:  # NOQA: PT011
        config_file.load(filepath=Path(tmp) / "test_data.unsupported")


def test_missing_file_extension_save() -> None:
    """test saving without a config file extension."""
    config_file = ConfigFile()
    with pytest.raises(ValueError), tempfile.TemporaryDirectory() as tmp:  # NOQA: PT011
        config_file.save(filepath=Path(tmp) / "test_data", config_dict=data)


def test_missing_file_extension_load() -> None:
    """test loading without a config file extension."""
    config_file = ConfigFile()

    with pytest.raises(ValueError), tempfile.TemporaryDirectory() as tmp:  # NOQA: PT011
        config_file.load(filepath=Path(tmp) / "test_data")
