# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from packaging.version import Version


class VersionUtils:
    @staticmethod
    def bump_major_version(version: Version) -> Version:
        """
        Increment the major version by 1 and zeroing the minor and patch versions and removing any pre,
        post, development, or local segments.  Preserves the epoch.
        """
        epoch_str = f"{version.epoch}!" if version.epoch else ""
        major = 0
        if len(version.release) >= 1:
            major = version.release[0]
        return Version(f"{epoch_str}{major + 1}.0.0")

    @staticmethod
    def bump_minor_version(version: Version) -> Version:
        """
        Increment the minor version by 1 and zeroing the patch version and removing any pre,
        post, development, or local segments.  Preserves the epoch and major version.
        """
        epoch_str = f"{version.epoch}!" if version.epoch else ""
        major: int = 0
        minor: int = 0
        if len(version.release) >= 1:
            major = version.release[0]
        if len(version.release) >= 2:
            minor = version.release[1]
        return Version(f"{epoch_str}{major}.{minor + 1}.0")

    @staticmethod
    def bump_patch_version(version: Version) -> Version:
        """
        Increment the patch (micro) version by 1 and removing any pre, post, development,
        or local segments.  Preserves the epoch and major version.
        """
        epoch_str = f"{version.epoch}!" if version.epoch else ""
        major: int = 0
        minor: int = 0
        patch: int = 0
        if len(version.release) >= 1:
            major = version.release[0]
        if len(version.release) >= 2:
            minor = version.release[1]
        if len(version.release) >= 3:
            patch = version.release[2]
        return Version(f"{epoch_str}{major}.{minor}.{patch + 1}")

    @staticmethod
    def max_version(version_str: str) -> Version:
        """
        Increment the version number to the upper bound of the version.
        Examples:
            "1.2.4" will be bumped to "2.0.0"
            "0.1.2" will be bumped to "0.2.0"
            "0.0.7" will be bumped to "0.0.8"
            "0 will bump to "1.0.0"
            "0.0 will bump to "0.1.0"
            "0.0.0 will bump to "0.1.0"
        """
        ver: Version = Version(version_str)
        if ver.major:
            ver = VersionUtils.bump_major_version(ver)
        elif ver.minor:
            ver = VersionUtils.bump_minor_version(ver)
        elif ver.micro:
            ver = VersionUtils.bump_patch_version(ver)
        elif len(ver.release) == 1:
            # 0 bumping to 1
            ver = VersionUtils.bump_major_version(ver)
        else:
            # 0.0 bumping to 0.1
            # and special case of 0.0.0 bumping to 0.1.0
            ver = VersionUtils.bump_minor_version(ver)
        return ver

    @staticmethod
    def fill_version_to_three_parts(version_str: str) -> str:
        """
        Fill out requirement to at least 3 parts, ex: 1.2 => 1.2.0
        """
        if not version_str:
            return "0.0.0"
        while len(version_str.split(".")) < 3:
            version_str += ".0"
        return version_str
