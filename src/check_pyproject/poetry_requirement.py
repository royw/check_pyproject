# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import re

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from check_pyproject.version_utils import VersionUtils


def caret_requirement_to_pep508(specification: str, *, max_bounds: bool = True) -> str:
    """
    Caret requirements allow SemVer compatible updates to a specified version. An update is allowed if the
    new version number does not modify the left-most non-zero digit in the major, minor, patch grouping.

    By default, an upper bound will be generated (ex:  "^1.2.3" becomes ">=1.2.3,<2.0.0").
    To disable this behavior, set max_bounds to False (ex:  "^1.2.3" becomes ">=1.2.3").
    """
    if max_bounds:
        return str(
            SpecifierSet(
                f">={VersionUtils.fill_version_to_three_parts(specification)}, "
                f"<{VersionUtils.fill_version_to_three_parts(str(VersionUtils.max_version(specification)))}"
            )
        )

    return str(SpecifierSet(f">={VersionUtils.fill_version_to_three_parts(specification)}"))


def tilde_requirement_to_pep508(specification: str) -> str:
    """
    Tilde requirements specify a minimal version with some ability to update. If you specify a major, minor,
    and patch version or only a major and minor version, only patch-level changes are allowed. If you only
    specify a major version, then minor- and patch-level changes are allowed.

    examples:
      "~1.2.3" becomes ">=1.2.3,<1.3.0"
      "~1.2" becomes ">=1.2.0, <1.3.0"
      "~1" becomes ">=1.0.0, <2.0.0"
    """
    ver: Version = Version(specification)
    ver = VersionUtils.bump_major_version(ver) if len(ver.release) == 1 else VersionUtils.bump_minor_version(ver)
    return str(
        SpecifierSet(
            f">={VersionUtils.fill_version_to_three_parts(specification)}, "
            f" <{VersionUtils.fill_version_to_three_parts(str(ver))}"
        )
    )


def wildcard_requirement_to_pep508(specification: str) -> str:
    """
    Wildcard requirements allow for the latest (dependency dependent) version where the wildcard
    is positioned. *, 1.* and 1.2.* are examples of wildcard requirements.

    examples:
    "*" becomes ">=0.0.0"
    "1*" becomes ">=1.0.0, <2.0.0"
    "1.2.*" becomes ">=1.2.0, <1.3.0"
    """
    if specification == "*":
        return str(SpecifierSet(f">={VersionUtils.fill_version_to_three_parts('0')}"))

    version_string: str = specification.rstrip("*").rstrip(".")  # ex: "1", "1.2"
    ver: Version = Version(version_string)

    if len(ver.release) == 1:
        ver = VersionUtils.bump_major_version(ver)
    elif len(ver.release) == 2:
        ver = VersionUtils.bump_minor_version(ver)

    return str(
        SpecifierSet(
            f">={VersionUtils.fill_version_to_three_parts(version_string)}, "
            f" <{VersionUtils.fill_version_to_three_parts(str(ver))}"
        )
    )


def convert_poetry_specifier_to_pep508(
    value: str | dict[str, str], *, max_bounds: bool = True, quotes: bool = False
) -> str:
    """
    Convert poetry dependency specifiers (^v.v, ~ v.v, v.*, <=v, > v, != v) to pep508 format
    returns a string containing comma separated pep508 specifiers
    """
    out: list[str] = []
    requirement: str
    if isinstance(value, str):
        value = re.sub(r"([\^~<>=!]+)\s+", r"\1", value)
        for requirement in re.split(r",\s*", value):
            # ^a.b.c
            if requirement.startswith("^"):
                out.append(caret_requirement_to_pep508(requirement[1:], max_bounds=max_bounds))
            elif requirement.startswith("~"):
                out.append(tilde_requirement_to_pep508(requirement[1:]))
            elif "*" in requirement:
                out.append(wildcard_requirement_to_pep508(requirement))
            else:
                out.append(str(SpecifierSet(VersionUtils.fill_version_to_three_parts(requirement))))

    result = ",".join(out)
    if quotes:
        result = re.sub(r"([~<>=!]+)(.+)", r'\1"\2"', result)

    return result
