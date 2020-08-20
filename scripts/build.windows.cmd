:: Copyright (c) Microsoft Corporation.
:: Licensed under the MIT License.

@echo off
rem Build script for Windows.  Used in Github Actions for continuous integration checks.
rem Note: "set Configuration={Release or Debug}" to switch the build type.

rem Move to the root of the repo.
pushd "%~dp0\.."

rem Setup the build environment.
call .\scripts\init.windows.cmd

rem Make style check failures fail the build.
set UncrustifyAutoFix=false

rem Build all .vcxproj and .csproj files listed in the various dirs.proj files.
rem Note: This also includes running unit tests.
msbuild /m /r dirs.proj

popd
@echo on
exit /B %ERRORLEVEL%
