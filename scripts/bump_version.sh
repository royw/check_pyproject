#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

# In the pyproject.toml file, bump the project.version and tool.poetry.version.
# If tool.poetry.version exists, it must match project.version, else error out.
# If tool.poetry.version exists but project.version does not, add project.version
# using the value of tool.poetry.version.

project_version=$(toml get --toml-path pyproject.toml project.version)
poetry_version=$(toml get --toml-path pyproject.toml tool.poetry.version)

echo "Initial versions:"
echo "project.version=${project_version}"
echo "poetry.version=${poetry_version}"

new_version=$(.venv/bin/bump2version --dry-run --allow-dirty --list --current-version "${project_version}" patch | sed -r s,"^.*=",,)

echo "New version: ${new_version}"
