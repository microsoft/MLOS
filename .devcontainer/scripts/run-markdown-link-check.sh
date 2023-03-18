#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

set -x

set -eu
scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir/"

# Build the helper container that has the cspell CLI.
#../build/build-devcontainer-cli.sh

# Make this work inside a devcontainer as well.
reporoot=$(readlink -f "$scriptdir/../../")
if [ -n "${LOCAL_WORKSPACE_FOLDER:-}" ]; then
    reporoot="$LOCAL_WORKSPACE_FOLDER"
fi

# Basically does what the markdown-link-check github action would do, but locally too.
# See Also: ~/.github/workflows/markdown-link-check.yml

docker run -i --rm \
    --user $(id -u):$(id -g) \
    -v "$reporoot":/src:ro \
    --workdir /src \
    markdown-link-check:latest \
    find ./doc ./mlos_core ./mlos_bench ./.devcontainer -name '*.md' -not -path './node_modules/*' \
        -exec markdown-link-check '{}' --config ./.github/workflows/markdown-link-check-config.json -q -v ';'

docker run -i --rm \
    --user $(id -u):$(id -g) \
    -v "$reporoot":/src:ro \
    --workdir /src \
    markdown-link-check:latest \
    find . -type f '(' -wholename ./CODE_OF_CONDUCT.md -o -wholename ./CONTRIBUTING.md -o -wholename ./README.md -o -wholename ./SECURITY.md ')' -not -path './node_modules/*' \
        -exec markdown-link-check '{}' --config ./.github/workflows/markdown-link-check-config.json -q -v ';'
