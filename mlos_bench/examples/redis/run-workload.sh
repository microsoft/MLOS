#!/bin/bash

set -eu

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"
source ./common.sh

# TODO: Run the client workload.
# Here we reuse the redis server container image, but replace its entrypoint with the redis-benchmark utility.
docker run --rm --name $REDIS_CLIENT_NAME --entrypoint /usr/local/bin/redis-benchmark $REDIS_IMAGE \
    -h $REDIS_SERVER_HOST -p $REDIS_PORT -t set

# TODO: Parse the results.
