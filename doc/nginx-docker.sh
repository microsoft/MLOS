#!/bin/bash

# A quick script to start a local webserver for testing the sphinx documentation.

scriptpath=$(readlink -f "$0")
scriptdir=$(dirname "$scriptpath")
cd "$scriptdir"

if [ "$1" == 'start' ]; then
    docker run -d --name mlos-doc-nginx -v $PWD/nginx-default.conf:/etc/nginx/conf.d/default.conf -v $PWD:/doc -p 8080:80 nginx
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
