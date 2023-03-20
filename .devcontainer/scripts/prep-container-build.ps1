# Requires -Version 3.0
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# A script to prepare the build environment for the devcontainer.

$ErrorActionPreference = 'Stop'

# Make sure we're in the root of the repository.
Set-Location "$PSScriptRoot/../.."

# Make sure the .env file exists for the devcontainer to load.
if (!(Test-Path .env)) {
    Write-Host "Creating empty .env file for devcontainer."
    New-Item -Type File .env
}

# Prep some files to use as context for the devcontainer to build from.
if (Test-Path .devcontainer/tmp) {
    Remove-Item -Recurse -Force .devcontainer/tmp
}
New-Item -Type Directory .devcontainer/tmp

Copy-Item conda-envs/mlos_core.yml .devcontainer/tmp/mlos_core.yml
foreach ($pkg in @('mlos_core', 'mlos_bench')) {
    New-Item -Type Directory ".devcontainer/tmp/${pkg}"
    Copy-Item "$pkg/setup.py" ".devcontainer/tmp/${pkg}/setup.py"
    Copy-Item "$pkg/_version.py" ".devcontainer/tmp/${pkg}/_version.py"
}
Copy-Item doc/requirements.txt .devcontainer/tmp/doc.requirements.txt

# Copy the script that will be run in the devcontainer to prep the files from
# those in a cross platform way (e.g. proper line endings and whatnot so that
# it's cacheable and reusable across platforms).
Copy-Item .devcontainer/scripts/common/prep-deps-files.sh .devcontainer/tmp/prep-deps-files.sh

# Prior to building the container locally, try to pull the latest version from
# upstream to see if we can use it as a cache.
# TODO: Ideally we'd only do this when rebuilding the image, but not sure how
# to detect that form of startup yet.
if ($env:NO_CACHE -ne 'true') {
    $cacheFrom = 'mloscore.azurecr.io/mlos-core-devcontainer'
    Write-Host "Pulling cached image $cacheFrom"
    docker pull $cacheFrom
}
