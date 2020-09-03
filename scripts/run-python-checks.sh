#!/bin/bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# Lint check the Python code

set -eu

# Start at the root of the repo.
scriptdir=$(readlink -f "$(dirname "$0")")
cd "$scriptdir/.."

. "$scriptdir/util.sh"
pythoncmd=`getPythonCmd`

cd source/Mlos.Python
$pythoncmd -m pylint --rcfile ../.pylintrc mlos
