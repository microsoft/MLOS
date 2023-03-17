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

docker run -i --rm \
    --user $(id -u):$(id -g) \
    -v "$reporoot":/src \
    --workdir /src \
    cspell \
    cspell lint --no-progress /src/
