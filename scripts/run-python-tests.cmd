:: Copyright (c) Microsoft Corporation.
:: Licensed under the MIT License.

@echo off
rem Run the Python unit tests.

rem Start at the root of the repo.
pushd "%~dp0\.."

rem Note: Windows filesystems are case insensitive so the -p "[Tt]est*.py"
rem argument isn't strictly necessary, but we keep it for parity with Linux.
pytest -svx -n 4 source\Mlos.Python

popd
@echo on
exit /B %ERRORLEVEL%
