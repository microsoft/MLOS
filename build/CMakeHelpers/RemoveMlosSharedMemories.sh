#!/bin/bash
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# A short script to remove any of the shared memory regions
# after finishing the unit tests.

# Be strict.
set -eu

scriptdir=$(dirname "$(readlink -f "$0")")
MLOS_ROOT=$(readlink -f "$scriptdir/../..")

. "$MLOS_ROOT/scripts/util.sh"

rm -f $Mlos_Shared_Memories
