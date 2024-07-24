#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

if [ $# -ne 1 ]
then
  echo "Usage:  $0 REGEX"
  exit 1
fi

git ls-files | grep -Ev ".pre-commit-config.yaml|Taskfile.*\.ya?ml|scripts/|.*\.md" | xargs grep -EH "$1"
[ $? -eq 123 ]
