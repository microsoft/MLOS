#!/bin/sh

# This is a simple script for CMake to invoke via execute_process() to find all
# of the *.cs files referenced by the *.csproj files in the working directory.
#
# We use this to help dynamically build up the set of dependencies for our
# CMakeLists.txt wrappers around .csproj files.

cat *.csproj 2>/dev/null \
    | egrep '<(Compile|SettingsRegistryDef) Include=".*\.cs"' \
    | sed -r -e 's/.*Include="([^"]+\.cs)".*/\1/' -e 's|\\|/|g' \
    | tr '\n' ';' | sed 's/;$//'

# Returns the full file name and path as specified in the Include
# attribute of the Compile directive.
