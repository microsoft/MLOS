#!/bin/sh

# This is a simple script for CMake to invoke via execute_process() to find all
# of the *.csproj files referenced by the *.csproj files in the working directory.
#
# We use this to help dynamically build up the set of dependencies for our
# CMakeLists.txt wrappers around .csproj files.

cat *.csproj 2>/dev/null \
    | grep '<ProjectReference Include=".*\.csproj"' \
    | sed -r -e 's|.*[/\\)"]([^"]+)\.csproj".*|\1|' \
    | tr '\n' ';' | sed 's/;$//'

# Returns just the name without the extension or its path as specified
# in the Include attribute of the ProjectReference directive.
