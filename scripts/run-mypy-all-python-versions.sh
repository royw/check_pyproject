#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

# this script will extract the python versions from .python-version,
# running mypy for each version.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

while read -r p; do
  ver=$(echo "$p" | grep -Eo "^[0-9]+\.[0-9]+")
  echo "mypy --strict --ignore-missing-imports --python-version=${ver} src/ tests/"
  mypy --strict --ignore-missing-imports --python-version="${ver}" src/ tests/
done < "${SCRIPT_DIR}/../.python-version"
