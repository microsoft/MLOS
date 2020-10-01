#!/bin/bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
# Fetches a recent cmake to the local repo's tools directory.

# Be more strict with variables and command exit codes.
set -eu
# Verbose debugging:
#set -x

version=3.17
build=3

script=$(readlink -f "$0")
scriptdir=$(dirname "$script")
cd "$scriptdir/.."
. ./scripts/util.sh

mkdir -p ./tools/bin
cd ./tools

bins='cmake cpack ctest'

# Check for local cmake first.
SYS_CMAKE='/usr/bin/cmake'
if [ -x "$SYS_CMAKE" ]; then
    CMAKE_INSTALLED_VERSION=$("$SYS_CMAKE" --version 2>&1 | head -n1 | sed 's/^cmake version //')
    if hasVersInstalled "$version.$build" "$CMAKE_INSTALLED_VERSION"; then
        echo "System cmake install is already up to date."

        # Cleanup the local versions and turn them into symlinks to the system
        # version instead so that all of the build scripts continue to work.
        rm -rf ./cmake
        mkdir -p ./cmake/bin
        for i in $bins; do
            rm -f ./bin/$i
            ln -s /usr/bin/$i ./bin/
            ln -s /usr/bin/$i ./cmake/bin/
            touch -r /usr/bin/$i -h ./bin/$i ./cmake/bin/$i
        done
        touch -r "$SYS_CMAKE" -h "$script"

        exit 0
    else
        cat >&2 <<-WARNMSG
        WARNING: system cmake version is too old.
        Please update your system (e.g. with apt-get) and rerun $0.
WARNMSG
        exit 1
        # Alternatively, we could also skip the exit here and let it fall
        # through to automatically installing a more up to date version in
        # tools/.
    fi
else
    echo "INFO: No system cmake installed.  Fetching a local verison for this repo." >&2
fi

echo "Fetching CMake $version.$build to local tools/ directory."

file="cmake-$version.$build.tar.gz"
url="https://cmake.org/files/v$version/$file"

file="cmake-$version.$build-Linux-x86_64.tar.gz"
url="https://github.com/Kitware/CMake/releases/download/v$version.$build/$file"
dir=$(basename $file .tar.gz)

#rm -f "$file"
wget --no-hsts -c -nc $url
rm -rf "./$dir"
tar -xzf "./$file"
rm -rf ./cmake
ln -s "./$dir" ./cmake

# Link the cmake tools into the tools/bin PATH.
mkdir -p ./bin
for i in $bins; do
    rm -f ./bin/$i
    ln -s ../cmake/bin/$i ./bin/
    # Touch the files so that any Makefile rules know that we're handled this already.
    test -e ./cmake/bin/$i && touch -h ./cmake/bin/$i ./bin/$i
done
