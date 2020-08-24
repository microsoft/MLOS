:: Copyright (c) Microsoft Corporation.
:: Licensed under the MIT License.

@echo off
rem Lint check the Python code

rem Start at the root of the repo.
pushd "%~dp0\.."

cd source\Mlos.Python
pylint --rcfile ..\.pylintrc mlos

popd
@echo on
exit /B %ERRORLEVEL%
