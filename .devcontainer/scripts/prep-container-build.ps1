# Requires -Version 3.0
# A script to prepare the build environment for the devcontainer.

$ErrorActionPreference = 'Stop'

# Make sure we're in the root of the repository.
Set-Location "$PSScriptRoot"

# Build a basic container with the dependencies we need to run the prep script.
docker build `
    -t mlos-core-basic-prep-deps `
    -f common/Dockerfile common/
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build mlos-core-basic-prep-deps container."
    exit $LASTEXITCODE
}
# Move up to the repo root.
Set-Location ../../
# Run the script in the container.
docker run --rm -v "${PWD}:/src" --workdir /src `
    --user root `
    mlos-core-basic-prep-deps `
    /src/.devcontainer/scripts/common/prep-container-build.sh
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to run prep-container-build.sh in container."
    exit $LASTEXITCODE
}

# Try to pull the cached image.
if ($env:NO_CACHE -ne 'true') {
    $cacheFrom = 'mloscore.azurecr.io/mlos-core-devcontainer'
    Write-Host "Pulling cached image $cacheFrom"
    docker pull $cacheFrom
}
