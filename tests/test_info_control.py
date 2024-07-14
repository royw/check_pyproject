# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

"""default tests for info_control.py"""

from __future__ import annotations

from check_pyproject.clibones.info_control import InfoControl


def test_version() -> None:
    info_control = InfoControl(app_package="check_pyproject")
    version: str = info_control._load_version()
    assert isinstance(version, str)
    assert len(version) > 0


def test_default_version() -> None:
    info_control = InfoControl(app_package=".")
    version: str = info_control._load_version()
    assert isinstance(version, str)
    assert len(version) > 0
    assert version == InfoControl.DEFAULT_VERSION


def test_longhelp() -> None:
    info_control = InfoControl(app_package="check_pyproject")
    longhelp: str = info_control._load_longhelp()
    assert longhelp is not None
    assert isinstance(longhelp, str)
    assert len(longhelp) > 0
    assert not longhelp.startswith("Long Help not available.")


def test_default_longhelp() -> None:
    info_control = InfoControl(app_package=".")
    longhelp: str = info_control._load_longhelp()
    assert longhelp is not None
    assert isinstance(longhelp, str)
    assert len(longhelp) > 0
    assert longhelp.startswith("Long Help not available.")
