#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# Layout a few markdown files from the source tree into the doc tree so they can be read there too.
# Fixup any links to point back to the main site though.

set -eu
set -x

scriptdir=$(dirname "$(readlink -f "$0")")
# Move to the repo root.
cd "$scriptdir/.."

rm -rf doc/source/source_tree_docs/
mkdir -p doc/source/source_tree_docs/

for readme_file_path in README.md mlos_core/README.md mlos_bench/README.md mlos_viz/README.md; do
    file_dir=$(dirname "$readme_file_path")
    mkdir -p "doc/source/source_tree_docs/$file_dir"

    cp "$readme_file_path" "doc/source/source_tree_docs/$file_dir/index.md"

    # Tweak source source code links.
    # FIXME: This sed expression doesn't work in MacOS.
    sed -i -r -e "s|\]\(([^:#)]+)(#[a-zA-Z0-9_-]+)?\)|\]\(https://github.com/microsoft/MLOS/tree/main/$file_dir/\1\2\)|g" \
        "doc/source/source_tree_docs/$file_dir/index.md"
    # Tweak the lexers for local expansion by pygments instead of github's.
    sed -i -r -e 's/```jsonc/```json/' \
        "doc/source/source_tree_docs/$file_dir/index.md"
done

# Do an explicit fixup for some static content.
sed -i -r -e 's#="[^"]*(_static/[^"]+)"#="../\1"#g' \
    "doc/source/source_tree_docs/index.md"
