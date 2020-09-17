#!/bin/bash
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# A wrapper script to run a command that makes use of the MLOS shared mem
# regions, and then cleans them up when it's done.short
# Used to work around not being able to run a shell oneliner in the
# add_test(COMMAND) definition in cmake.

# Be strict.
set -eu

scriptdir=$(dirname "$(readlink -f "$0")")
MLOS_ROOT=$(readlink -f "$scriptdir/../..")

if [ -z "${1:-}" ]; then
    echo "Missing test command args!" >&2
fi

$* && $MLOS_ROOT/build/CMakeHelpers/RemoveMlosSharedMemories.sh
