# Requires -Version 5.0
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# A script to build the mlos_core and mlos_bench wheels and test them.

$ErrorActionPreference = 'Stop'

if (!($env:CONDA_ENV_NAME)) {
    $env:CONDA_ENV_NAME = 'mlos'
}

# Make sure we're in the root of the repository.
Set-Location "$PSScriptRoot/../.."

# Build the mlos_core wheel.
Set-Location mlos_core
if (Test-Path dist) {
    Remove-Item -Recurse -Force dist
}
conda run -n $env:CONDA_ENV_NAME python -m build
Set-Location ..
$mlos_core_whl = (Resolve-Path mlos_core/dist/mlos_core-*-py3-none-any.whl | Select-Object -ExpandProperty Path)
Write-Host "mlos_core_whl: $mlos_core_whl"
if (!($mlos_core_whl)) {
    Write-Error "Failed to find mlos_core wheel."
    exit 1
}

# Build the mlos_bench wheel.
Set-Location mlos_bench
if (Test-Path dist) {
    Remove-Item -Recurse -Force dist
}
conda run -n $env:CONDA_ENV_NAME python -m build
Set-Location ..
$mlos_bench_whl = (Resolve-Path mlos_bench/dist/mlos_bench-*-py3-none-any.whl | Select-Object -ExpandProperty Path)
Write-Host "mlos_bench_whl: $mlos_bench_whl"
if (!($mlos_bench_whl)) {
    Write-Error "Failed to find mlos_bench wheel."
    exit 1
}

# Build the mlos_viz wheel.
Set-Location mlos_viz
if (Test-Path dist) {
    Remove-Item -Recurse -Force dist
}
conda run -n $env:CONDA_ENV_NAME python -m build
Set-Location ..
$mlos_viz_whl = (Resolve-Path mlos_viz/dist/mlos_viz-*-py3-none-any.whl | Select-Object -ExpandProperty Path)
Write-Host "mlos_viz_whl: $mlos_viz_whl"
if (!($mlos_viz_whl)) {
    Write-Error "Failed to find mlos_viz wheel."
    exit 1
}

# Setup a clean environment to test installing/using them.
$PythonVersReq = (conda list -n $env:CONDA_ENV_NAME | Select-String -AllMatches -Pattern '^python\s+([0-9]+\.[0-9]+)[0-9.]*\s+').Matches.Groups[1].Value
#$PythonVersReq = conda run -n $env:CONDA_ENV_NAME python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "Python version required: $PythonVersReq"
conda create -y -v -n mlos-dist-test python=${PythonVersReq}
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create mlos-dist-test conda env."
    exit $LASTEXITCODE
}
conda install -y -v -n mlos-dist-test vswhere vs2019_win-64
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install compiler dependencies."
    exit $LASTEXITCODE
}
# Add a few extras we have to pull in from conda-forge.
# See Also: mlos-windows.yml
conda install -y -v -n mlos-dist-test swig libpq
# FIXME: conda on Windows doesn't appear to respect ">=0.9.0" as a version constraint despite various quoting tweaks.
conda install -y -v -n mlos-dist-test -c conda-forge 'pyrfr=0.9'
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install pyrfr dependencies."
    exit $LASTEXITCODE
}

# Install mlos_core wheel.
conda run -n mlos-dist-test pip install "${mlos_core_whl}[full-tests]"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install mlos_core wheels."
    exit $LASTEXITCODE
}
# Install mlos_bench wheel.
conda run -n mlos-dist-test pip install "${mlos_bench_whl}[full-tests]"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install mlos_bench wheels."
    exit $LASTEXITCODE
}
# Install mlos_viz wheel.
conda run -n mlos-dist-test pip install "${mlos_viz_whl}[full-tests]"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install mlos_viz wheels."
    exit $LASTEXITCODE
}

# Just pick one simple test to run for now.
# The rest should have been handled in a separate step.
conda run -n mlos-dist-test python -m pytest mlos_core/mlos_core/tests/spaces/spaces_test.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to run mlos_core tests."
    exit $LASTEXITCODE
}

# Run a simple mlos_bench test.
conda run -n mlos-dist-test python -m pytest mlos_bench/mlos_bench/tests/environments/mock_env_test.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to run mlos_bench tests."
    exit $LASTEXITCODE
}

# Run a simple mlos_viz test.
# To do that, we need the fixtures from mlos_bench, so make those available too.
$env:PYTHONPATH = "mlos_bench"
conda run -n mlos-dist-test python -m pytest mlos_viz/mlos_viz/tests/test_dabl_plot.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to run mlos_viz tests."
    exit $LASTEXITCODE
}
