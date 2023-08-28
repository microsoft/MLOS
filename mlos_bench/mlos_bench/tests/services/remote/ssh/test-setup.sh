#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

set -eu

set -x

network_name=mlos_bench-ssh-test-network
server_name=mlos_bench-ssh-test-server
client_name=mlos_bench-ssh-test-client
image_name="$server_name"
timeout=900
# Use an alternative port than the default 22 to avoid conflicts with the host.
port=2222

# Create a network for the containers to communicate on.
docker network create "$network_name" || true

# Setup the container to listen on a different port.
docker build -t "$image_name" \
    --build-arg PORT="$port" \
    --build-arg http_proxy=${http_proxy:-} \
    --build-arg https_proxy=${https_proxy:-} \
    --build-arg no_proxy=${no_proxy:-} \
    -f Dockerfile .

docker rm --force "$server_name" || true
docker run -d --rm --env TIMEOUT=$timeout --network="$network_name" --name "$image_name" "$server_name"

# TODO: Do this in the python code:
# Run a simple test client to connect to the server.
docker run -it --rm --network="$network_name" "$image_name" \
    ssh -o StrictHostKeyChecking=accept-new -p $port "$server_name" \
    hostname
