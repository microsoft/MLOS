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
docker rm --force $REDIS_CLIENT_NAME 2>/dev/null || true

# To setup the workload, for now, we only need to pull the image.
docker pull $REDIS_IMAGE
