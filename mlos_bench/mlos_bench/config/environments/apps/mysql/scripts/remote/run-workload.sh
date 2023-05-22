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
# Here we reuse the mysql server container image, but replace its entrypoint with the mysql-benchmark utility.
docker run --rm --name $MYSQL_CLIENT_NAME --entrypoint /usr/local/bin/mysql-benchmark $MYSQL_IMAGE \
    -h $MYSQL_SERVER_HOST -p $MYSQL_PORT \
    -t set \
    -q --csv \
    | tee /tmp/mlos_bench/output/results.csv
