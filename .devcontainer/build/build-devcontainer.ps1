# Requires -Version 5.0
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# A script to build the devcontainer image.

$ErrorActionPreference = 'Stop'

# Make sure we're in the root of the repository.
Set-Location "$PSScriptRoot"

# Build the helper container that has the devcontainer CLI for building the devcontainer.

./build-devcontainer-cli.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build devcontainer-cli container."
    exit $LASTEXITCODE
}

# Build the devcontainer image.

$rootdir = Resolve-Path "$PSScriptRoot/../.." | Select-Object -ExpandProperty Path

# Run the initialize command on the host first.
# Note: command should already pull the cached image if possible.
$initializeCommand = Get-Content "$rootdir/.devcontainer/devcontainer.json" | ConvertFrom-Json | Select-Object -ExpandProperty initializeCommand
if (!($initializeCommand)) {
    Write-Error "No initializeCommand found in devcontainer.json"
    exit 1
}
else {
    $origLocation = Get-Location
    Set-Location "$rootdir/"
    Write-Host "Running: $initializeCommand"
    Invoke-Expression -Verbose "$initializeCommand"
    Set-Location "$origLocation"
}

if ($null -eq $env:DOCKER_BUILDKIT) {
    $env:DOCKER_BUILDKIT = 1
}
$devcontainer_build_args = ''
if ("$env:NO_CACHE" -eq 'true') {
    $base_image = (Get-Content "$rootdir/.devcontainer/Dockerfile" | Select-String '^FROM' | Select-Object -ExpandProperty Line | ForEach-Object { $_ -replace '^FROM\s+','' } | ForEach-Object { $_ -replace ' AS\s+.*','' } | Select-Object -First 1)
    docker pull --platform linux/amd64 $base_image
    $devcontainer_build_args = '--no-cache'
}
else {
    $cacheFrom = 'mloscore.azurecr.io/mlos-devcontainer:latest'
    $devcontainer_build_args = "--cache-from $cacheFrom"
    docker pull --platform linux/amd64 "$cacheFrom"
}

# Make this work inside a devcontainer as well.
if ($env:LOCAL_WORKSPACE_FOLDER) {
    $rootdir = $env:LOCAL_WORKSPACE_FOLDER
}

$cmd = "docker run -i --rm " +
    "--user root " +
    "-v '${rootdir}:/src' " +
    "-v /var/run/docker.sock:/var/run/docker.sock " +
    "--env DOCKER_BUILDKIT=${env:DOCKER_BUILDKIT} " +
    "--env BUILDKIT_INLINE_CACHE=1 " +
    "devcontainer-cli " +
    "devcontainer build --workspace-folder /src " +
    "$devcontainer_build_args " +
    "--image-name mlos-devcontainer:latest"
Write-Host "Running: $cmd"
Invoke-Expression -Verbose "$cmd"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build devcontainer."
    exit $LASTEXITCODE
}
