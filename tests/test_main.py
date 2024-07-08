# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from importlib.metadata import version
from pathlib import Path
from typing import Any

import pytest
from _pytest.capture import CaptureFixture

from check_pyproject.__main__ import main


def test_main_pyproject() -> None:
    assert main([str(Path(__file__).parent / "good_pyproject.toml")]) == 0


def test_main_bad_pyproject() -> None:
    assert main([str(Path(__file__).parent / "bad_pyproject.toml")]) != 0


def test_main_version(capsys: CaptureFixture[Any]) -> None:
    assert main(["--version"]) == 0
    captured = capsys.readouterr()
    assert version("check_pyproject") in captured.err


def test_main_longhelp() -> None:
    assert main(["--longhelp"]) == 0


def test_main_help(capsys: CaptureFixture[Any]) -> None:
    # --help is handled from argparse
    # this testing pattern from: https://dev.to/boris/testing-exit-codes-with-pytest-1g27
    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.type is SystemExit
    assert e.value.code == 0
    captured = capsys.readouterr()
    assert "--version" in captured.out


def test_load_config_file(capsys: CaptureFixture[Any]) -> None:
    tests_dir = Path(__file__).parent

    # with debug=true
    assert main(["--config", str(tests_dir / "config_1.toml"), str(tests_dir / "good_pyproject.toml")]) == 0
    captured = capsys.readouterr()
    assert "project_requirements" in captured.err

    # with debug=false
    assert main(["--config", str(tests_dir / "config_2.toml"), str(tests_dir / "good_pyproject.toml")]) == 0
    captured = capsys.readouterr()
    assert "project_requirements" not in captured.err


def test_debug_flag(capsys: CaptureFixture[Any]) -> None:
    tests_dir = Path(__file__).parent

    # with debug=true
    assert main(["--debug", str(tests_dir / "good_pyproject.toml")]) == 0
    captured = capsys.readouterr()
    assert "project_requirements" in captured.err

    # with debug=false
    assert main([str(tests_dir / "good_pyproject.toml")]) == 0
    captured = capsys.readouterr()
    assert "project_requirements" not in captured.err
