#!/bin/bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
# Fetches a recent dotnet to the local repo's directory.

# Be more strict with variables and command exit codes.
set -eu
# Verbose debugging:
#set -x

DOTNET_VERSION='3.1.201'

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir/.."
mkdir -p ./tools
TOOLS_DIR=$(readlink -f ./tools)

. ./scripts/util.sh

###########################################################################
# INSTALL .NET CORE CLI
###########################################################################

. ./scripts/dotnet.env

DOTNET_DIR="$TOOLS_DIR/dotnet"
mkdir -p "$DOTNET_DIR"

DOTNET="$DOTNET_DIR/dotnet"
DOTNET_INSTALLED_VERSION=$("$DOTNET" --version 2>/dev/null || true)

if ! hasVersInstalled "$DOTNET_VERSION" "$DOTNET_INSTALLED_VERSION"; then
    echo "Cleaning up previous .NET install ..."
    rm -rf "$DOTNET_DIR"
    mkdir -p "$DOTNET_DIR"
    rm -f ./tools/bin/dotnet
    echo "Installing .NET CLI ..."
    curl -Lsfo "$DOTNET_DIR/dotnet-install.sh" https://dot.net/v1/dotnet-install.sh
    bash "$DOTNET_DIR/dotnet-install.sh" --version $DOTNET_VERSION --install-dir "$DOTNET_DIR" --no-path
else
    echo "Local .NET install is already up to date."
fi

# Link our dotnet wrapper script into to the tools/bin PATH.
mkdir -p ./tools/bin
rm -f ./tools/bin/dotnet
ln -s ../../scripts/dotnet ./tools/bin/
# Touch the files so that any Makefile rules know that we're handled this already.
for i in ./tools/dotnet/dotnet ./tools/bin/dotnet; do
    test -e $i && touch $i
done
