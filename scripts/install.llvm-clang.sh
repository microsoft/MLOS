#!/usr/bin/env bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
# A simple helper script to make sure an appropriate version of clang is installed.

set -eu

scriptdir=$(dirname "$(readlink -f "$0")")
MLOS_ROOT=$(readlink -f "$scriptdir/..")

CLANG_VERSION="10"
CLANG_PKG="clang-${CLANG_VERSION}"
CLANG_BIN="clang-${CLANG_VERSION}"

if [ "$(type $CLANG_BIN 2>/dev/null)" == "" ]; then
    echo "Missing Clang $CLANG_VERSION ..."

    echo "Updating local apt-cache ..."
    set -x
    sudo apt-get update >/dev/null
    set +x
    if apt-cache show $CLANG_PKG | grep -q "^Package: $CLANG_PKG"; then
        echo "Installing $CLANG_PKG via apt ..."
        # Try to install it via the existing package manager:
        set -x
        sudo apt-get -y install $CLANG_PKG
        set +x
    else
        # Else, we need to add repositories for the current distro we're on.

        sudo apt-get -y --no-install-recommends install \
            curl lsb-release wget software-properties-common

        TOOLS_DIR="$MLOS_ROOT/tools"
        mkdir -p "$TOOLS_DIR"

        echo "$CLANG_PKG not available via apt, adding LLVM repositories ..."
        curl -Lsfo "$TOOLS_DIR/llvm.sh" "https://apt.llvm.org/llvm.sh"
        set -x
        sudo bash "$TOOLS_DIR/llvm.sh" "$CLANG_VERSION"
        set +x
    fi
else
    echo "$CLANG_BIN is already available."
fi
