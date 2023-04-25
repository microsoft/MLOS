#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# Script to store old grub config and reboot VM (if necessary).
# Config file created in scheduler should have been moved to
# VM BEFORE this script is run.
# This script should be run in the VM.

set -eu

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"
source ./common-boot-time.sh

# remove original boot time parameters file if it exists
rm -f "$ORIG_BOOT_TIME"

# create copy of original boot-time parameters
cp /etc/default/grub.cfg "$ORIG_BOOT_TIME"
update-grub

# check if the real config file has changed
if diff -u /boot/grub/grub.cfg "$ORIG_BOOT_TIME"; then
  reboot
fi
