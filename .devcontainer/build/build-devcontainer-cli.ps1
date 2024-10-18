# Requires -Version 5.0
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# A script to build the devcontainer-cli image.

$ErrorActionPreference = 'Stop'

# Make sure we're in the root of the repository.
Set-Location "$PSScriptRoot"

# Build the helper container that has the devcontainer CLI for building the devcontainer.

docker ps > $null
if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: docker ps failed.  Make sure docker is running."
    exit 1
}

if ($null -eq $env:DOCKER_BUILDKIT) {
    $env:DOCKER_BUILDKIT = 1
}
$devcontainer_cli_build_args = ''
docker buildx version > $null
if ($LASTEXITCODE -eq 0) {
    $devcontainer_cli_build_args += ' --progress=plain'
}
else {
    Write-Warning 'NOTE: docker buildkit unavailable.'
}

if ("$env:NO_CACHE" -eq 'true') {
    $devcontainer_cli_build_args += ' --no-cache --pull'
}
else {
    $cacheFrom = 'mloscore.azurecr.io/devcontainer-cli:latest'
    $devcontainer_cli_build_args += " --cache-from $cacheFrom"
    docker pull --platform linux/amd64 $cacheFrom
}

$cmd = "docker.exe build -t devcontainer-cli:latest -t cspell:latest " +
    "--build-arg BUILDKIT_INLINE_CACHE=1 " +
    "$devcontainer_cli_build_args " +
    "-f Dockerfile ."
Write-Host "Running: $cmd"
Invoke-Expression -Verbose "$cmd"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build devcontainer-cli container."
    exit $LASTEXITCODE
}
