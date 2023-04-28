#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# Quick hacky script to start a devcontainer in a non-vscode shell for testing.
# See Also:
# - ../build/build-devcontainer
# - "devcontainer open" subcommand from <https://github.com/devcontainers/cli>

set -eu

# Move to repo root.
scriptdir=$(dirname "$(readlink -f "$0")")
repo_root=$(readlink -f "$scriptdir/../..")
repo_name=$(basename "$repo_root")
cd "$repo_root"

container_name="$repo_name.$(stat -c%i "$repo_root/")"

mkdir -p "/tmp/$container_name/dc/shellhistory"
docker run -it --rm \
    --name "$container_name" \
    --user vscode \
    -v "$HOME/.azure":/dc/azure \
    -v "/tmp/$container_name/dc/shellhistory:/dc/shellhistory" \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$PWD":"/workspaces/$repo_name" \
    --workdir "/workspaces/$repo_name" \
    --env CONTAINER_WORKSPACE_FOLDER="/workspaces/$repo_name" \
    --env LOCAL_WORKSPACE_FOLDER="$repo_root" \
    --env http_proxy="${http_proxy:-}" \
    --env https_proxy="${https_proxy:-}" \
    --env no_proxy="${no_proxy:-}" \
    mlos-devcontainer
