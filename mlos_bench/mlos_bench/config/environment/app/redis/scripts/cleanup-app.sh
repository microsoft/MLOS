#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

set -eu

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"
source ./common.sh

# Stop the container.
docker stop $REDIS_SERVER_NAME
