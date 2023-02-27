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

docker build -t devcontainer-cli:latest -t cspell:latest --progress=plain \
    $devcontainer_cli_build_args \
    --build-arg NODE_UID=$(id -u) \
    --build-arg NODE_GID=$(id -g) \
    --build-arg DOCKER_GID=$DOCKER_GID \
    --build-arg http_proxy=${http_proxy:-} \
    --build-arg https_proxy=${https_proxy:-} \
    --build-arg no_proxy=${no_proxy:-} \
    -f Dockerfile .
if [ "${CONTAINER_REGISTRY:-}" != '' ]; then
    docker tag devcontainer-cli:latest "$CONTAINER_REGISTRY/devcontainer-cli:latest"
fi
