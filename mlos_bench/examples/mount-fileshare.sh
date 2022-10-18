#!/bin/bash

set -eu
set -o pipefail

if [ $EUID != 0 ]; then
    echo "ERROR: This script expects to be executed with root privileges." >&2
    exit 1
fi

if ! mountpoint -q /mnt/osat-fs; then
    mount -t cifs //$storageAccountName.file.core.windows.net/$storageFileShareName /mnt/osat-fs \
        -o username=$storageAccountName,password=$storageAccountKey,dir_mode=0777,file_mode=0777,serverino,nosharesock,actimeo=30
fi