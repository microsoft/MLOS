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

echo "Fetching CMake $version.$build to tools/ directory."

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir/.."
mkdir -p ./tools
cd ./tools

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
for i in cmake cmake-gui ccmake cpack ctest; do
    rm -f ./bin/$i
    ln -s ../cmake/bin/$i ./bin/
    # Touch the files so that any Makefile rules know that we're handled this already.
    test -e ./cmake/bin/$i && touch ./cmake/bin/$i ./bin/$i
done
