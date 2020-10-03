# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
# A small helper script to setup the shell environment to use our local
# versions of tools (e.g. cmake, dotnet, etc.)
#
# Note: this is not required, but then the other tools should be available on
# the system PATH.

sourced=''
if [ -n "$BASH_VERSION" ]; then
    if [[ $0 != $BASH_SOURCE ]]; then
        sourced="$BASH_SOURCE"
    fi
elif [ -n "$ZSH_VERSION" ]; then
    if [[ $ZSH_EVAL_CONTEXT =~ :file$ ]]; then
        sourced="$0"
    fi
else
    echo "ERROR This script needs to be sourced and currently only works using bash or zsh shells." >&2
    return 1
fi

if [ -z "$sourced" ]; then
    echo "Please 'source' this file instead of running it:" >&2
    echo "# . $0" >&2
    exit 1
fi

scriptdir=$(dirname "$(readlink -f "$sourced")")
MLOS_ROOT=$(readlink -f "$scriptdir/..")

# Add the local tools dir to the PATH.
export PATH="$PATH:$MLOS_ROOT/tools/bin"

# Make sure cmake is available.
if ! type cmake >/dev/null; then
    echo "Missing cmake.  Please run '$MLOS_ROOT/scripts/install.cmake.sh && $MLOS_ROOT/scripts/setup.cmake.sh." >&2
    return -1
fi

# Make sure dotnet is available.
if ! type dotnet >/dev/null; then
    echo "Missing dotnet.  Please run '$MLOS_ROOT/scripts/install.cmake.sh && $MLOS_ROOT/scripts/setup.cmake.sh." >&2
    return -1
fi
. "$MLOS_ROOT/scripts/dotnet.env"
