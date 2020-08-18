# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

#Requires -Version 2.0

#
#  MSBuild Environment Initialization
#
#    Forwards command line arguments to init.windows.cmd and captures environment
#    variable changes to set within the current PowerShell session.
#

[CmdletBinding()]
param
(
    # Use cmdlet binding to support default parameters like -v.
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]] $Arguments
)

$dp0 = Split-Path -Parent $MyInvocation.MyCommand.Path
$tmpFile = [System.IO.Path]::GetTempFileName()

if (!($env:MLOS_ROOT) -or !(Test-Path -Type Container $env:MLOS_ROOT))
{
    Write-Host ('Missing or invalid $env:MLOS_ROOT: "{0}".' -f $env:MLOS_ROOT)
    $env:MLOS_ROOT = (Resolve-Path "$dp0/..").Path
    Write-Host ('Defaulting to current directory.')
}

Write-Verbose "Calling `"$dp0\init.windows.cmd`" $Arguments to save environment variables in $tmpFile."
cmd /c "call `"$dp0\init.windows.cmd`" $Arguments && set > `"$tmpFile`""
if ($LASTEXITCODE -ne 0) {
    Remove-Item -Force $tmpFile
    throw 'Error running init.windows.cmd'
}

Write-Verbose "Parsing environment variables from `"$tmpFile`" to current PowerShell session."
Get-Content $tmpFile | ForEach-Object {
    $props = $_ -split '=', 2

    Write-Verbose "Setting variable `"$($props[0])`": $($props[1])"
    [System.Environment]::SetEnvironmentVariable($props[0], $props[1])
}
Remove-Item -Force $tmpFile
