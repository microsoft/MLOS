#!/bin/bash

# Layout markdown files from the source tree into the doc tree so they can be read there too.

set -eu
set -x

scriptdir=$(dirname "$(readlink -f "$0")")
# Move to the repo root.
cd "$scriptdir/.."

rm -rf doc/source/source_tree_docs/
mkdir -p doc/source/source_tree_docs/

find -name '*.md' \
    | egrep -v -e '^./(doc|.pytest_cache)/' \
    | while read file_path; do
    file_dir=$(dirname "$file_path")
    file_name=$(basename "$file_path")

    mkdir -p "doc/source/source_tree_docs/$file_dir"
    cp "$file_path" "doc/source/source_tree_docs/$file_dir/"

    # Make README.md files look like index.html files.
    if [ "$file_name" == "README.md" ]; then
        ln -s "README.md" "doc/source/source_tree_docs/$file_dir/index.md"
    fi

    # Tweak some directory links.
    sed -i -r -e 's|([a-z])/\)|\1/README.md\)|g' "doc/source/source_tree_docs/$file_dir/$file_name"
    # Tweak source source code links.
    sed -i -r -e "s#\(([^)]+[.](py|json|jsonc))\)#\(https://github.com/microsoft/MLOS/tree/main/$file_dir/\1\)#g" \
        "doc/source/source_tree_docs/$file_dir/$file_name"
done

# Find directory symlinks and recreate those too.
find -H -type l -xtype d \
    | egrep -v -e '^./(doc|.pytest_cache)/' \
    | while read link_path; do
        link_dir=$(dirname "$link_path")
        link_name=$(basename "$link_path")
        link_target=$(readlink "$link_path")
        mkdir -p "doc/source/source_tree_docs/$link_dir"
        (cd "doc/source/source_tree_docs/$link_dir" && ln -s "$link_target" "$link_name")
    done

