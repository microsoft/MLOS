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

script=$(readlink -f "$0")
scriptdir=$(dirname "$script")
cd "$scriptdir/.."
mkdir -p ./tools
TOOLS_DIR=$(readlink -f ./tools)

. ./scripts/util.sh
. ./scripts/dotnet.env

SYS_DOTNET='/usr/bin/dotnet'
DOTNET_DIR="$TOOLS_DIR/dotnet"
mkdir -p "$DOTNET_DIR"
mkdir -p "$TOOLS_DIR/bin"

# First, check to see if there's a system version of dotnet installed.
if [ -x "$SYS_DOTNET" ]; then
    DOTNET_INSTALLED_VERSION=$("$SYS_DOTNET" --version)
    if hasVersInstalled "$DOTNET_VERSION" "$DOTNET_INSTALLED_VERSION"; then
        echo "System .NET install is already up to date."

        # Cleanup the local versions and turn them into symlinks to the system
        # version instead so that all of the build scripts continue to work.
        rm -rf "$DOTNET_DIR"
        mkdir -p "$DOTNET_DIR"
        ln -s "$SYS_DOTNET" "$DOTNET_DIR/"
        rm -f "$TOOLS_DIR/bin/dotnet"
        ln -s "$SYS_DOTNET" "$TOOLS_DIR/bin/"

        # Setup is done.  Let make know by adjusting the timestamps to match
        # the system dotnet file (including this script).
        touch -r "$SYS_DOTNET" -h "$DOTNET_DIR/dotnet"
        touch -r "$SYS_DOTNET" -h "$TOOLS_DIR/bin/dotnet"
        touch -r "$SYS_DOTNET" -h "$script"

        exit 0
    else
        cat >&2 <<-WARNMSG
        WARNING: system dotnet version is too old.
        Please update your system (e.g. with apt-get) and rerun $0.
WARNMSG
        exit 1
        # Alternatively, we could also skip the exit here and let it fall
        # through to automatically installing a more up to date version in
        # tools/.
    fi
else
    echo "INFO: No system dotnet installed.  Fetching a local verison for this repo." >&2
fi

###########################################################################
# INSTALL LOCAL .NET CORE CLI
###########################################################################

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
    test -e $i && touch -h $i
done
