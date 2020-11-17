:: Copyright (c) Microsoft Corporation.
:: Licensed under the MIT License.

@echo off
rem Package script for Windows.  Used in Github Actions for continuous integration checks.
rem Note: "set Configuration={Release or Debug}" to switch the build type.

rem Move to the root of the repo.
pushd "%~dp0\.."

rem Setup the build environment.
call .\scripts\init.windows.cmd

rem Use msbuild to effectively call "dotnet pack" on a number of projects.
msbuild /m /r .\source\Mlos.NetCore.Components.Packages\Mlos.NetCore.Components.Packages.proj
rem Now, use those to build an external integration example project.
dotnet build .\external\ExternalIntegrationExample\ExternalIntegrationExample.SettingsRegistry\ExternalIntegrationExample.SettingsRegistry.csproj

popd
@echo on
exit /B %ERRORLEVEL%
