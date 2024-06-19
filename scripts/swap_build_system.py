# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

import sys

import tomlkit
from pathlib import Path

from tomlkit import TOMLDocument


def usage(progname: str):
    print(f"Usage: {progname} hatch|poetry")
    print(f"  {progname} hatch will switch the build-system to hatchling.")
    print(f"  {progname} poetry will switch the build-system to poetry-core.")


def main():
    if len(sys.argv) < 2:
        usage(sys.argv[0])
        return 1

    if sys.argv[1] not in ("hatch", "poetry"):
        usage(sys.argv[0])
        return 1

    pyproject_path = Path("pyproject.toml")
    with pyproject_path.open(encoding="utf-8") as f:
        doc: TOMLDocument = tomlkit.load(f)
        if sys.argv[1] == "hatch":
            doc["build-system"]["requires"] = ["hatchling", "hatch-vcs"]
            doc["build-system"]["build-backend"] = "hatchling.build"
        elif sys.argv[1] == "poetry":
            doc["build-system"]["requires"] = ["poetry-core>=1.0.0"]
            doc["build-system"]["build-backend"] = "poetry.core.masonry.api"
    with pyproject_path.open(mode="wt", encoding="utf-8") as save:
        save.write(tomlkit.dumps(doc))

    return 0


if __name__ == '__main__':
    sys.exit(main())
