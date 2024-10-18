#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

set -x

set -eu
scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir/"

source ../common.sh

# Build the helper container that has the devcontainer CLI for building the devcontainer.

if [ ! -w /var/run/docker.sock ]; then
    echo "ERROR: $USER does not have write access to /var/run/docker.sock. Please add $USER to the docker group." >&2
    exit 1
fi
DOCKER_GID=$(stat $STAT_FORMAT_GID_ARGS /var/run/docker.sock)
# Make this work inside a devcontainer as well.
if [ -w /var/run/docker-host.sock ]; then
    DOCKER_GID=$(stat $STAT_FORMAT_GID_ARGS /var/run/docker-host.sock)
fi

export DOCKER_BUILDKIT=${DOCKER_BUILDKIT:-1}
devcontainer_cli_build_args=''
if docker buildx version 2>/dev/null; then
    devcontainer_cli_build_args+=' --progress=plain'
else
    echo 'NOTE: docker buildkit unavailable.' >&2
fi

if [ "${NO_CACHE:-}" == 'true' ]; then
    devcontainer_cli_build_args+=' --no-cache --pull'
else
    cacheFrom='mloscore.azurecr.io/devcontainer-cli'
    tmpdir=$(mktemp -d)
    devcontainer_cli_build_args+=" --cache-from $cacheFrom"
    docker --config="$tmpdir" pull "$cacheFrom" || true
    rmdir "$tmpdir"
fi

docker build -t devcontainer-cli:latest -t cspell:latest -t markdown-link-check:latest \
    $devcontainer_cli_build_args \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
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
