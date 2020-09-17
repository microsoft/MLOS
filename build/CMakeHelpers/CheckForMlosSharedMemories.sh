#!/bin/bash
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# A short script to check if any of the shared memory regions already exist
# before starting unit tests.

# Be strict.
set -eu

scriptdir=$(dirname "$(readlink -f "$0")")
MLOS_ROOT=$(readlink -f "$scriptdir/../..")

. "$MLOS_ROOT/scripts/util.sh"

for i in $Mlos_Shared_Memories; do
    if [ -e "$i" ]; then
        echo "WARNING: '$i' already exists. Check to see if it's no longer in use and then remove it." >&2
        exit 1
    fi
done

exit 0
