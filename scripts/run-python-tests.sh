#!/bin/bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# Run the Python unit tests.

set -eu

# Start at the root of the repo.
scriptdir=$(readlink -f "$(dirname "$0")")
cd "$scriptdir/.."

. "$scriptdir/util.sh"
pythoncmd=`getPythonCmd`

# Linux filesystems are case-sensitive, so we need to tell the python unit test
# scanner to look for upper-case files as well:
$pythoncmd -m unittest discover --verbose --locals --failfast -s source/Mlos.Python -p "[Tt]est*.py" $*
