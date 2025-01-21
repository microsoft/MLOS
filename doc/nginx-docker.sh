#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# A quick script to start a local webserver for testing the sphinx documentation.

set -eu

scriptpath=$(readlink -f "$0")
scriptdir=$(dirname "$scriptpath")
cd "$scriptdir"

SKIP_NGINX_BUILD=${SKIP_NGINX_BUILD:-false}

if [ -f ../.devcontainer/.env ]; then
    source ../.devcontainer/.env
fi
NGINX_PORT="${NGINX_PORT:-81}"

# Make it work inside a devcontainer too.
repo_root=$(readlink -f "$scriptdir/..")
if [ -n "${LOCAL_WORKSPACE_FOLDER:-}" ]; then
    repo_root="$LOCAL_WORKSPACE_FOLDER"
fi

cmd="${1:-}"

if [ "$cmd" == 'start' ]; then
    set -x
    tmpdir=$(mktemp -d)
    if ! $SKIP_NGINX_BUILD; then
        docker build --progress=plain -t mlos-doc-nginx \
            --build-arg http_proxy=${http_proxy:-} \
            --build-arg https_proxy=${https_proxy:-} \
            --build-arg no_proxy=${no_proxy:-} \
            --build-arg NGINX_PORT=$NGINX_PORT \
            -f Dockerfile "$tmpdir"
        rmdir "$tmpdir"
    fi
    docker run -d --name mlos-doc-nginx \
        -v "$repo_root/doc/nginx-default.conf":/etc/nginx/templates/default.conf.template \
        -v "$repo_root/doc":/doc \
        --env NGINX_PORT=$NGINX_PORT \
        -p 8080:$NGINX_PORT \
        mlos-doc-nginx
    set +x
elif [ "$cmd" == 'stop' ]; then
    docker stop mlos-doc-nginx || true
    docker rm mlos-doc-nginx || true
elif [ "$cmd" == 'restart' ]; then
    "$scriptpath" 'stop'
    "$scriptpath" 'start'
else
    echo "ERROR: Invalid argument: $0." >&2
    echo "Usage: $0 [start|stop|restart]"
    exit 1
fi
