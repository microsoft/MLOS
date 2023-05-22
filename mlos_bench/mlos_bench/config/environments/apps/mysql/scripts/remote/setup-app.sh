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

# Remove any previously running/failed instances.
docker rm --force $MYSQL_SERVER_NAME 2>/dev/null || true

# Start the MYSQL server container in the background and expose it's port on the host machine.
# TODO: Explore use of -v /data volume mount for persisting snapshots.
# TODO: Explore how to map different server configs in.
docker run -d --rm --name $MYSQL_SERVER_NAME -p $MYSQL_PORT:$MYSQL_PORT $MYSQL_IMAGE
