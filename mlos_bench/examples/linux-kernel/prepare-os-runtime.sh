#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# Script to apply new runtime parameters of booted VM.
# This script should be run in the VM.

set -eu

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"
source ./common-runtime.sh

# remove original boot time parameters file if it exists
rm -f "$ORIG_CONFIG_FILE"

# For all of the paths that we change, save their original settings for restoration later.
cat "$PATHS_FILE" | while read path; do
  echo ""$path":$(cat "$path")"
done > "$ORIG_CONFIG_FILE"

# Apply new runtime parameters
cat "$RUNTIME_PARAMS" | while read line; do
    key=$(echo "$line" | cut -f 1)
    val=$(echo "$line" | cut -f 2-)
    echo "$val" > "$key"
done
