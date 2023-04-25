#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# Script to restore boot-time parameters of VM to original state.
# This script should be run in the VM.

set -eu

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"
source ./common-boot-time.sh

# remove our addins file and regenerate the config file
rm -f "$ORIG_BOOT_TIME"
update-grub

# check if the real config file has changed
if diff -u /boot/grub/grub.cfg "$ORIG_BOOT_TIME"; then
  reboot
fi
