#!/usr/bin/env bash
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# Be more strict with variables and command exit codes.
#set -eu
# Verbose debugging:
##set -x

# Build with Cake using DotNet.Core

# Define directories.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TOOLS_DIR="$SCRIPT_DIR/tools"

# Define default arguments.
SCRIPT="$SCRIPT_DIR/build.cake"
CAKE_VERSION="0.37.0"
CLANG_VERSION="10"
CAKE_ARGUMENTS=()

# Parse arguments.
for i in "$@"; do
    case $1 in
        -s|--script) SCRIPT="$2"; shift ;;
        --cake-version) CAKE_VERSION="--version=$2"; shift ;;
        --) shift; CAKE_ARGUMENTS+=("$@"); break ;;
        *) CAKE_ARGUMENTS+=("$1") ;;
    esac
    shift
done

# Make sure the tools folder exists
if [ ! -d "$TOOLS_DIR" ]; then
    mkdir "$TOOLS_DIR"
fi

# Make sure that cmake and dotnet are available and on the path.
source "$SCRIPT_DIR/scripts/init.linux.sh"

###########################################################################
# INSTALL CAKE
###########################################################################

CAKE_PATH="$TOOLS_DIR/dotnet-cake"
CAKE_INSTALLED_VERSION=$($CAKE_PATH --version 2>&1 || true)

if [ "$CAKE_VERSION" != "$CAKE_INSTALLED_VERSION" ]; then
    if [ -f "$CAKE_PATH" ]; then
        dotnet tool uninstall Cake.Tool --tool-path "$TOOLS_DIR"
    fi

    echo "Installing Cake $CAKE_VERSION..."
    dotnet tool install Cake.Tool --tool-path "$TOOLS_DIR" --version $CAKE_VERSION

    if [ $? -ne 0 ]; then
        echo "An error occured while installing Cake."
        exit 1
    fi
fi

export CC=/usr/bin/clang-$CLANG_VERSION
export CXX=/usr/bin/clang++-$CLANG_VERSION

$CXX --version

###########################################################################
# RUN BUILD SCRIPT
###########################################################################
exec "$CAKE_PATH" "$SCRIPT" "${CAKE_ARGUMENTS[@]}"
