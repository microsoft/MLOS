#!/usr/bin/env bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
# A simple helper script to make sure an appropriate version of python is installed.

set -eu

scriptdir=$(dirname "$(readlink -f "$0")")
MLOS_ROOT=$(readlink -f "$scriptdir/..")

PYTHON_VERSION="3.7"
PYTHON_PKG="python${PYTHON_VERSION}"
PYTHON_BIN="python${PYTHON_VERSION}"

if [ "$(type $PYTHON_BIN 2>/dev/null)" == "" ]; then
    echo "Missing Python $PYTHON_VERSION ..."

    echo "Updating local apt-cache ..."
    set -x
    sudo apt-get update >/dev/null
    set +x
    if ! apt-cache show $PYTHON_PKG | grep -q "^Package: $PYTHON_PKG"; then
        # We need to add extra repositories for the current distro we're on.
        set -x
        sudo apt-get -y --no-install-recommends install software-properties-common apt-transport-https
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt-get update
        set +x
    fi

    echo "Installing $PYTHON_PKG via apt ..."
    # Try to install it via the existing package manager:
    set -x
    sudo apt-get --no-install-recommends -y install $PYTHON_PKG ${PYTHON_PKG}-dev
    set +x
else
    echo "$PYTHON_BIN is already available."
fi

if ! [ -x /usr/bin/pip3 ]; then
    echo "Installing missing pip3 via local apt-get ..."
    set -x
    sudo apt-get update
    sudo apt-get -y install python3-pip
    set +x
fi
