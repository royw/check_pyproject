# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

"""
Simple script to swap build systems in pyproject.toml.

Usage:

    python swap_build_system.py [hatch|poetry|setuptool]

will change the build system in pyproject.toml to:

    [build-system]
    requires = [...]
    build-backend = "..."
"""

import sys
import tempfile
from argparse import ArgumentParser
from typing import Sequence

import tomlkit
from pathlib import Path
from tomlkit import TOMLDocument

SUPPORTED_BUILD_SYSTEMS = {
    "hatch": {
        "requires": ["hatchling", "hatch-vcs"],
        "build-backend": "hatchling.build",
    },
    "poetry": {
        "requires": ["poetry-core>=1.0.0"],
        "build-backend": "poetry.core.masonry.api",
    },
    "setuptools": {
        "requires": ["setuptools >= 65",
                     "wheel >= 0.38",
                     ],
        "build-backend": "setuptools.build_meta",
    }
}


def main(args: Sequence[str]) -> int:
    """
    Swap build systems in pyproject.toml.
    param: args expects the equivalent of sys.argv[1:]
    """
    parser = ArgumentParser(description="Swap build systems in pyproject.toml")
    parser.add_argument("--pyproject-toml", type=Path, required=False, default="pyproject.toml",
                        help="Path to the pyproject.toml file. (default: pyproject.toml)")
    parser.add_argument("build_system_name", choices=SUPPORTED_BUILD_SYSTEMS.keys(),
                        help="The name of the build system to switch to.")
    settings, remaining_args = parser.parse_known_args(args=args)

    # update pyproject.toml with desired build-system.
    pyproject_path = settings.pyproject_toml
    with pyproject_path.open(encoding="utf-8") as f:
        doc: TOMLDocument = tomlkit.load(f)
        doc["build-system"]["requires"] = SUPPORTED_BUILD_SYSTEMS[settings.build_system_name]["requires"]
        doc["build-system"]["build-backend"] = SUPPORTED_BUILD_SYSTEMS[settings.build_system_name]["build-backend"]

    # write to temporary file then atomically "switch" it with the original using rename.
    with tempfile.NamedTemporaryFile('wt', dir=pyproject_path.parent, delete=False) as tf:
        tf.write(tomlkit.dumps(doc))
        temp_name = Path(tf.name)
    temp_name.rename(pyproject_path)
    return 0


if __name__ == '__main__':
    sys.exit(main(args=sys.argv[1:]))
