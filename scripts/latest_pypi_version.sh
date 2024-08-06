#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

# get the current version of the given package(s) from pypi and output as PEP508 dependency specifier(s)

for package_name in "$@"
do
    version=$(curl --silent "https://pypi.org/pypi/{$package_name}/json" | jq -r .info.version)
    if [[ ${version} == null ]]; then
      echo "${package_name} was not found on pypi.org"
    else
      echo "${package_name}>=${version}"
    fi
done
