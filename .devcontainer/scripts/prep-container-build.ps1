# Requires -Version 3.0
# A script to prepare the build environment for the devcontainer.

$ErrorActionPreference = 'Stop'

# Make sure we're in the root of the repository.
Set-Location "$PSScriptRoot/../../"

# Make sure the .env file exists for the devcontainer to load.
if (!(Test-Path -PathType Leaf '.env')) {
    Write-Host "Creating empty .env file for devcontainer."
    New-Item -ErrorAction SilentlyContinue -Type File -Name '.env'
}

# Create (partial) conda environment file for the container to build from.
# Note: this should make it more cacheable as well.
# See Also: updateContentCommand in .devcontainer/devcontainer.json
Write-Host "Creating base mlos_core_deps.yml environment file for devcontainer context."
if (Test-Path '.devcontainer/tmp') {
    Remove-Item -Recurse '.devcontainer/tmp'
}
New-Item -Type Directory -Name '.devcontainer/tmp'
# Powershell equivalent of dos2unix and grep/sed to make the content match that of the Linux side.
Get-Content './conda-envs/mlos_core.yml' `
    | ForEach-Object { $_ -replace '#.*','' } `
    | Select-String -NotMatch -Pattern '--editable','^\s*$' `
    | Set-Content -Encoding ascii './.devcontainer/tmp/mlos_core_deps.yml.tmp'
Get-Content './.devcontainer/tmp/mlos_core_deps.yml.tmp' -Raw `
    | ForEach-Object { $_ -replace "`r","" } `
    | Set-Content -Encoding ascii -NoNewline './.devcontainer/tmp/mlos_core_deps.yml'
Remove-Item './.devcontainer/tmp/mlos_core_deps.yml.tmp'
Get-Content './.devcontainer/tmp/mlos_core_deps.yml'
try {
    # For some reason when started from pwsh, the powershell that gets launched
    # inside vscode is an older version that doesn't include this command.
    # It's not a requirement, just helpful for debugging non-cached builds, so
    # we ignore it for now if it's not available.
    Get-FileHash -Algorithm MD5 './.devcontainer/tmp/mlos_core_deps.yml'
}
catch {
    Write-Host "Get-FileHash not available. Skipping."
}

# Try to pull the cached image.
if ($env:NO_CACHE -ne 'true') {
    try {
        $cacheFrom = ((Get-Content ./.devcontainer/devcontainer.json | ForEach-Object { $_ -replace '//.*','' } | ConvertFrom-Json).build.cacheFrom)
        if (!($cacheFrom)) {
            $cacheFrom = 'mloscore.azurecr.io/mlos-core-devcontainer'
        }
        Write-Host "Pulling cached image $cacheFrom"
        docker pull $cacheFrom
    }
    catch {
        Write-Host "Failed to parse or pull cacheFrom from .devcontainer/devcontainer.json"
    }
}
