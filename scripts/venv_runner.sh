#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

# simple script to activate the .venv virtual environment, run the passed command, deactivate the virtual environment
# returns the exit code from the passed command
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ACTIVATE="${SCRIPT_DIR}/../.venv/bin/activate"

# make sure activate file exists, if not return error
if ! test -f "${ACTIVATE}"; then
  echo "Virtual Environment activate file (${ACTIVATE}) not found!"
  exit 1
fi

# shellcheck source=/dev/null
source "${ACTIVATE}"
"$@"
exit_code=$?
deactivate
exit "${exit_code}"
