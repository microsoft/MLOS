#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# A script to start a local docker container image for testing SSH services.

set -eu
set -x

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"

network_name='mlos_bench-ssh-test-network'
server_name='mlos_bench-ssh-test-server'
server_fqdn=$server_name
client_name='mlos_bench-ssh-test-client'
image_name="$server_name"
timeout=${timeout:-180}
# Use an alternative port than the default 22 to avoid conflicts with the host.
port=2254

#network_name='host'
#server_fqdn='host.docker.internal'

if ! docker ps | awk '{ print $NF }' | grep -q "$server_name"; then
    echo "SSH test server container $server_name not found. Creating it."

    docker network create "$network_name" || true

    # Setup the container to listen on a different port.
    docker build -t "$image_name" \
        --build-arg PORT="$port" \
        --build-arg http_proxy=${http_proxy:-} \
        --build-arg https_proxy=${https_proxy:-} \
        --build-arg no_proxy=${no_proxy:-} \
        -f Dockerfile . \
        || { echo "Failed to build SSH test server image $image_name."; exit 1; }

    docker rm --force "$server_name" || true
    docker run -d --rm \
        --env TIMEOUT=$timeout \
        --add-host "host.docker.internal:host-gateway" \
        --network="$network_name" \
        -p $port:$port \
        --name "$image_name" \
        "$server_name" \
        || { echo "Failed to start local SSH test server container $server_name."; exit 1; }
    sleep 1
fi

# Run a simple test client to connect to the server.
docker run -it --rm --network="$network_name" "$image_name" \
    ssh -o StrictHostKeyChecking=accept-new -p $port "$server_fqdn" \
    hostname \
    || { echo "Failed to connect to local SSH test server container listening at $server_fqdn on port $port"; exit 1; }
