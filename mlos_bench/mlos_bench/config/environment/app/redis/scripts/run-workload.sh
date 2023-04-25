#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

set -eu

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"
source ./common.sh

check_docker

# Run the client workload.
# Here we reuse the redis server container image, but replace its entrypoint with the redis-benchmark utility.
docker run --rm --name $REDIS_CLIENT_NAME --entrypoint /usr/local/bin/redis-benchmark $REDIS_IMAGE \
    -h $REDIS_SERVER_HOST -p $REDIS_PORT \
    -t set \
    -q --csv \
    | tee /tmp/mlos_bench/output/results.csv
