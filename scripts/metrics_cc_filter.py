#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

"""
Combine file name with method for all functions/methods with complex complexity B-F

Usage:

    poetry run -- radon cc --show-complexity --min=A src/ --json | scripts/metrics_cc_filter.py

"""
import json
import re
import sys
from typing import Sequence


def main(argv: Sequence[str]) -> int:
    def recurse_tree(tree: dict):
        result = []
        for branch in tree:
            if 'name' in branch:
                name = branch['name']
                if 'classname' in branch:
                    name = f"{branch['classname']}.{name}"
                result.append(name)
                if "method" in branch:
                    result.extend(recurse_tree(branch['method']))
                result[-1] = f"{result[-1]}:{branch['lineno']} {branch['rank']} ({branch['complexity']})"
        return result

    if len(argv) == 2:
        with open(argv[1]) as fp:
            data = json.loads(fp.read())
    else:
        data = json.loads(sys.stdin.read())

    lines: list[str] = []
    for filename in data.keys():
        for method in recurse_tree(data[filename]):
            lines.append(f"{filename}:{method}")

    lines.sort(reverse=True, key=lambda x: int(re.match(r".*\((\d+)\)$", x).group(1)))
    for line in lines:
        match = re.match(r".*\((\d+)\)$", line)
        if match:
            if int(match[1]) > 5:
                print(line)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
