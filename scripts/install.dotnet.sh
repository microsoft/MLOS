#!/usr/bin/env bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
# A simple helper script to make install dotnet in the system.
# See Also: https://docs.microsoft.com/en-us/dotnet/core/install/linux-ubuntu

set -eu

if ! [ -x /usr/bin/dotnet ] || [ "${1:-}" == '--force-upgrade' ]; then
    wget -q -O /tmp/packages-microsoft-prod.deb "https://packages.microsoft.com/config/ubuntu/`lsb_release -r -s`/packages-microsoft-prod.deb"
    set -x
    sudo dpkg -i /tmp/packages-microsoft-prod.deb
    sudo apt-get update
    sudo apt-get --no-install-recommends -y install dotnet-sdk-3.1 dotnet-runtime-3.1 aspnetcore-runtime-3.1
    set +x
else
    echo '/usr/bin/dotnet is already available.  Use "apt-get update && apt-get upgrade" to update it.'
fi
