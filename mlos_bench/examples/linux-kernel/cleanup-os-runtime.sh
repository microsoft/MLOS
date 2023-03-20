#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# Script to restore runtime parameters of VM to original state.
# This script should be run in the VM.

set -eu

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"
source ./common-runtime.sh

# access original runtime parameters, parse file, and restore to original state
cat "$ORIG_CONFIG_FILE" | while read line; do
    key_path=$(echo "$line" | cut -d: -f1)
    orig_val=$(echo "$line" | cut -d: -f2-)
    echo "$orig_val" > "$key_path"
done

# remove original runtime parameters file
rm -f "$ORIG_CONFIG_FILE"
