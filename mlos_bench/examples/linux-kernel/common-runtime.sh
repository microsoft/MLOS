##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# Environment variables and root access for runtime parameters.
# This file should be in the VM.

# check for root access
if [ $EUID != 0 ]; then
    echo "ERROR: This script expects to be executed with root privileges." >&2
    exit 1
fi

# Script to apply new runtime parameters
RUNTIME_PARAMS="${RUNTIME_PARAMS:-runtime_params.tsv}"

# File to store original runtime parameters
ORIG_CONFIG_FILE="${ORIG_CONFIG_FILE:-orig_val.txt}"

# File to store paths that will be changed
PATHS_FILE="${PATHS_FILE:-paths.txt}"
