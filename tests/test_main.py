# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from pathlib import Path

import pytest

from check_pyproject.__main__ import main


def test_main_pyproject() -> None:
    assert main([str(Path(__file__).parent / "good_pyproject.toml")]) == 0


def test_main_version() -> None:
    assert main(["--version"]) == 0


def test_main_longhelp() -> None:
    assert main(["--longhelp"]) == 0


def test_main_help() -> None:
    # --help is handled from argparse
    # this testing pattern from: https://dev.to/boris/testing-exit-codes-with-pytest-1g27
    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.type is SystemExit
    assert e.value.code == 0
