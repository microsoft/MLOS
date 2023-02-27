#!/bin/bash

set -x

set -eu
scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir/"

# Build the helper container that has the devcontainer CLI for building the devcontainer.
./build-devcontainer-cli.sh

DOCKER_GID=$(stat -c'%g' /var/run/docker.sock)
# Make this work inside a devcontainer as well.
if [ -w /var/run/docker-host.sock ]; then
    DOCKER_GID=$(stat -c'%g' /var/run/docker-host.sock)
fi

# Build the devcontainer image.
rootdir=$(readlink -f "$scriptdir/../..")

# Run the initialize command on the host first.
# Note: command should already pull the cached image if possible.
pwd
devcontainer_json=$(cat "$rootdir/.devcontainer/devcontainer.json" | sed -e 's|//.*||' -e 's|/\*|\n&|g;s|*/|&\n|g' | sed -e '/\/\*/,/*\//d')
initializeCommand=$(echo "$devcontainer_json" | docker run -i --rm devcontainer-cli jq -e -r '.initializeCommand[]')
if [ -z "$initializeCommand" ]; then
    echo "No initializeCommand found in devcontainer.json" >&2
    exit 1
else
    eval "pushd "$rootdir/"; $initializeCommand; popd"
fi

devcontainer_build_args=''
if [ "${NO_CACHE:-}" == 'true' ]; then
    devcontainer_build_args='--no-cache'
else
    cacheFrom='mloscore.azurecr.io/mlos-core-devcontainer'
    #devcontainer_build_args="--cache-from $cacheFrom"
    docker pull "$cacheFrom" || true
fi

# Make this work inside a devcontainer as well.
if [ -n "${LOCAL_WORKSPACE_FOLDER:-}" ]; then
    rootdir="$LOCAL_WORKSPACE_FOLDER"
fi

docker run -i --rm \
    --user $(id -u):$DOCKER_GID \
    -v "$rootdir":/src \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --env http_proxy=${http_proxy:-} \
    --env https_proxy=${https_proxy:-} \
    --env no_proxy=${no_proxy:-} \
    devcontainer-cli \
    devcontainer build --workspace-folder /src \
        $devcontainer_build_args \
        --image-name mlos-core-devcontainer
if [ "${CONTAINER_REGISTRY:-}" != '' ]; then
    docker tag mlos-core-devcontainer:latest "$CONTAINER_REGISTRY/mlos-core-devcontainer:latest"
fi
