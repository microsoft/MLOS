#!/bin/bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# Run the Python unit tests.

set -eu

# Start at the root of the repo.
scriptdir=$(readlink -f "$(dirname "$0")")
cd "$scriptdir/.."

pytest -svxl -n auto source/Mlos.Python --cov=mlos --cov-report=xml $*
