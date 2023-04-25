##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# Environment variables, distribution check, root access for boot-time parameters.
# This file should be in the VM.

# check for supported distribution
if ! lsb_release -i -s | grep -q -i -x -e ubuntu -e debian; then
    echo "ERROR: Unsupported distribution: $(lsb_release -i -s)" >&2;
    exit 1;
fi

# check for root access
if [ $EUID != 0 ]; then
    echo "ERROR: This script expects to be executed with root privileges." >&2
    exit 1
fi

# file of old boot-time parameters
ORIG_BOOT_TIME="${ORIG_BOOT_TIME:-/boot/grub/grub.cfg.bak}"
