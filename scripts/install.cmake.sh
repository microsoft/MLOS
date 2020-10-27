#!/usr/bin/env bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
# A simple helper script to make install cmake in the system.
# See Also: https://apt.kitware.com/

set -eu

if ! [ -x /usr/bin/cmake ] || [ "${1:-}" == '--force-upgrade' ]; then
    wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null | gpg --dearmor - | sudo tee /etc/apt/trusted.gpg.d/kitware.gpg >/dev/null
    set -x
    sudo apt-add-repository "deb https://apt.kitware.com/ubuntu/ `lsb_release -c -s` main"
    sudo apt-get update
    sudo apt-get --no-install-recommends -y install cmake
    set +x
else
    echo '/usr/bin/cmake is already available.  Use "apt-get update && apt-get upgrade" to update it.'
fi
