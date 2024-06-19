# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

"""
Simple script to swap build systems in pyproject.toml.

Usage:

    python swap_build_system.py poetry

will change the build system in pyproject.toml to:

    [build-system]
    requires = ["poetry-core>=1.0.0"]
    build-backend = "poetry.core.masonry.api"

while:

    python swap_build_system.py hatch

will change the build system in pyproject.toml to:

    [build-system]
    requires = ["hatchling", "hatch-vcs"]
    build-backend = "hatchling.build"


"""

import sys
import tempfile

import tomlkit
from pathlib import Path
from tomlkit import TOMLDocument


def usage(progname: str) -> None:
    print(f"Usage: {progname} hatch|poetry")
    print(f"  {progname} hatch will switch the build-system to hatchling.")
    print(f"  {progname} poetry will switch the build-system to poetry-core.")


def main() -> int:
    # require positional argument of either "poetry" or "hatch".  Show usage otherwise.
    if len(sys.argv) != 2 or sys.argv[1] not in ("hatch", "poetry"):
        usage(sys.argv[0])
        return 1

    # update pyproject.toml with desired build-system.
    pyproject_path = Path("pyproject.toml")
    with pyproject_path.open(encoding="utf-8") as f:
        doc: TOMLDocument = tomlkit.load(f)
        if sys.argv[1] == "hatch":
            doc["build-system"]["requires"] = ["hatchling", "hatch-vcs"]
            doc["build-system"]["build-backend"] = "hatchling.build"
        elif sys.argv[1] == "poetry":
            doc["build-system"]["requires"] = ["poetry-core>=1.0.0"]
            doc["build-system"]["build-backend"] = "poetry.core.masonry.api"

    # write to temporary file then atomically "switch" it with the original using rename.
    with tempfile.NamedTemporaryFile('wt', dir=pyproject_path.parent, delete=False) as tf:
        tf.write(tomlkit.dumps(doc))
        temp_name = Path(tf.name)
    temp_name.rename(pyproject_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
