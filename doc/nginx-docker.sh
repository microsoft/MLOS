#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# A quick script to start a local webserver for testing the sphinx documentation.

scriptpath=$(readlink -f "$0")
scriptdir=$(dirname "$scriptpath")
cd "$scriptdir"

# Make it work inside a devcontainer too.
repo_root=$(readlink -f "$scriptdir/..")
if [ -n "${LOCAL_WORKSPACE_FOLDER:-}" ]; then
    repo_root="$LOCAL_WORKSPACE_FOLDER"
fi

if [ "$1" == 'start' ]; then
    set -x
    docker build --progress=plain -t mlos-doc-nginx \
        --build-arg http_proxy=$http_proxy \
        --build-arg https_proxy=$https_proxy \
        --build-arg no_proxy=$no_proxy \
        -f Dockerfile /dev/null
    docker run -d --name mlos-doc-nginx \
        -v "$repo_root/doc/nginx-default.conf":/etc/nginx/conf.d/default.conf \
        -v "$repo_root/doc":/doc \
        -p 8080:80 \
        mlos-doc-nginx
    set +x
elif [ "$1" == 'stop' ]; then
    docker stop mlos-doc-nginx || true
    docker rm mlos-doc-nginx || true
elif [ "$1" == 'restart' ]; then
    "$scriptpath" 'stop'
    "$scriptpath" 'start'
else
    echo "ERROR: Invalid argument: $0." >&2
    echo "Usage: $0 [start|stop|restart]"
    exit 1
fi
