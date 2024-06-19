# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from pathlib import Path

import check_pyproject.__main__


def test_main():
    assert check_pyproject.__main__.main([str(Path(__file__).parent / "good_pyproject.toml")]) == 0
    assert check_pyproject.__main__.main(["--version"]) == 0
    assert check_pyproject.__main__.main(["--longhelp"]) == 0
