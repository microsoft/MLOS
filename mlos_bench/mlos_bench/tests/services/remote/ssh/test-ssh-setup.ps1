# Requires -Version 5.0
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# A script to start a local docker container image for testing SSH services.

$ErrorActionPreference = 'Stop'

Set-Location "$PSScriptRoot"

$server_name = 'mlos_bench-ssh-test-server'
$client_name = 'mlos_bench-ssh-test-client'
$image_name = "$server_name"
$timeout = 180
# Use an alternative port than the default 22 to avoid conflicts with the host.
$port = 2254

if (!(docker ps | Select-String -Pattern "$server_name")) {
    Write-Host "SSH test server container $server_name not found. Creating it."

    # Setup the container to listen on a different port.
    docker build -t "$image_name" \
        --build-arg PORT="$port" \
        --build-arg http_proxy=${http_proxy:-} \
        --build-arg https_proxy=${https_proxy:-} \
        --build-arg no_proxy=${no_proxy:-} \
        -f Dockerfile .
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build server image."
        exit $LASTEXITCODE
    }

    docker rm --force "$server_name"
    docker run -d --rm --env TIMEOUT=$timeout --network=host --name "$image_name" "$server_name"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start server."
        exit $LASTEXITCODE
    }
    Start-Sleep -Seconds 1
}

# Run a simple test client to connect to the server.
docker run -it --rm --network=host "$image_name" \
    ssh -o StrictHostKeyChecking=accept-new -p $port localhost \
    hostname
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to connect to server."
    exit $LASTEXITCODE
}
