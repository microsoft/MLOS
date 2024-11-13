#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# Quick hacky script to start a devcontainer in a non-vscode shell for testing.
# See Also:
# - ../build/build-devcontainer
# - "devcontainer open" subcommand from <https://github.com/devcontainers/cli>

#Set-PSDebug -Trace 2
$ErrorActionPreference = 'Stop'

# Move to repo root.
Set-Location "$PSScriptRoot/../.."
$repo_root = (Get-Item . | Select-Object -ExpandProperty FullName)
$repo_name = (Get-Item . | Select-Object -ExpandProperty Name)
$repo_root_id = $repo_root.GetHashCode()
$container_name = "$repo_name.$repo_root_id"

# Be sure to use the host workspace folder if available.
$workspace_root = $repo_root

$docker_gid = 0

New-Item -Type Directory -ErrorAction Ignore "${env:TMP}/$container_name/dc/shellhistory"

docker run -it --rm `
    --name "$container_name" `
    --user vscode `
    --env USER=vscode `
    --group-add $docker_gid `
    -v "${env:USERPROFILE}/.azure:/dc/azure" `
    -v "${env:TMP}/$container_name/dc/shellhistory:/dc/shellhistory" `
    -v "/var/run/docker.sock:/var/run/docker.sock" `
    -v "${workspace_root}:/workspaces/$repo_name" `
    --workdir "/workspaces/$repo_name" `
    --env CONTAINER_WORKSPACE_FOLDER="/workspaces/$repo_name" `
    --env LOCAL_WORKSPACE_FOLDER="$workspace_root" `
    --env http_proxy="${env:http_proxy:-}" `
    --env https_proxy="${env:https_proxy:-}" `
    --env no_proxy="${env:no_proxy:-}" `
    mlos-devcontainer `
    $args
