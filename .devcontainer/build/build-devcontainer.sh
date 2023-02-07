#!/bin/bash

set -x

set -eu
scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir/"

# Build the helper container that has the devcontainer CLI for building the devcontainer.

if [ ! -w /var/run/docker.sock ]; then
    echo "ERROR: $USER does not have write access to /var/run/docker.sock. Please add $USER to the docker group." >&2
    exit 1
fi
DOCKER_GID=$(stat -c'%g' /var/run/docker.sock)
# Make this work inside a devcontainer as well.
if [ -w /var/run/docker-host.sock ]; then
    DOCKER_GID=$(stat -c'%g' /var/run/docker-host.sock)
fi

devcontainer_cli_build_args=''
if [ "${NO_CACHE:-}" == 'true' ]; then
    devcontainer_cli_build_args='--no-cache --pull'
else
    #devcontainer_cli_build_args='--cache-from mloscore.azurecr.io/devcontainer-cli'
    docker pull mloscore.azurecr.io/devcontainer-cli || true
fi

docker build -t devcontainer-cli \
    $devcontainer_cli_build_args \
    --build-arg NODE_UID=$(id -u) \
    --build-arg NODE_GID=$(id -g) \
    --build-arg DOCKER_GID=$DOCKER_GID \
    --build-arg http_proxy=${http_proxy:-} \
    --build-arg https_proxy=${https_proxy:-} \
    --build-arg no_proxy=${no_proxy:-} \
    -f Dockerfile .

# Build the devcontainer image.
rootdir=$(readlink -f "$scriptdir/../..")

# Run the initialize command on the host first.
# Note: command should already pull the cached image if possible.
pwd
initializeCommand=$(cat ../devcontainer.json | sed 's|//.*||' | docker run -i --rm devcontainer-cli jq -e -r '.initializeCommand[]')
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
    if type jq >/dev/null 2>&1; then
        pwd
        cacheFrom=$(cat ../devcontainer.json | sed 's|//.*||' | docker run -i --rm devcontainer-cli jq -e -r .build.cacheFrom | grep -v -x -e null | cat)
    fi
    if [ -z "${cacheFrom:-}" ]; then
        cacheFrom='mloscore.azurecr.io/mlos-core-devcontainer'
    fi
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
        --image-name mlos-core-devcontainer \
