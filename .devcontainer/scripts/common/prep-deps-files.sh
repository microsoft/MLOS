#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# Prep some files for the devcontainer build in a way that's cross platform.
# We do this by running this script from a container that has the tools we need
# and generates files with the right encodings so that it's more cacheable
# across platforms.

set -eu
set -o pipefail

set -x

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"

cat /tmp/conda-tmp/mlos.yml \
    | sed 's|#.*||' \
    | egrep -v -e '--editable' -e '^\s*$' \
    | tee /tmp/conda-tmp/mlos_deps.yml

# Try to grab the requirements.txt files for the python packages.
tmpdir=$(mktemp -d)
get_python_deps() {
    local pkg="$1"
    touch /tmp/conda-tmp/$pkg.requirements.txt
    (cd /tmp/conda-tmp/$pkg && python3 setup.py egg_info --egg-base "$tmpdir/")
    cat "$tmpdir/$pkg.egg-info/requires.txt" \
        | grep -v -e '^\[' -e '^\s*$' \
        | grep -v '^mlos-' \
        | sort -u \
        > /tmp/conda-tmp/$pkg.requirements.txt
}
for pkg in mlos_core mlos_bench mlos_viz; do
    get_python_deps "$pkg"
done
rm -rf "$tmpdir"
cat /tmp/conda-tmp/*.requirements.txt | sort -u | tee /tmp/conda-tmp/combined.requirements.txt
