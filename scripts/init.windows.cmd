:: Copyright (c) Microsoft Corporation.
:: Licensed under the MIT License.

@echo off
rem Setup the current shell environment for building with tools from Visual Studio on Windows.
rem Without this the path probably won't contain things like: msbuild, cl, devenv, etc.
rem See Also: Prerequisites.md

if "%__VSCMD_PREINIT_PATH%" == "" goto CheckMlosRootEnv
rem else ...
echo ERROR: This shell has already been initialized for building with VS.
goto error

:CheckMlosRootEnv
rem Check for MLOS_ROOT environment variable.
if "%MLOS_ROOT%" == "" goto SetMlosRoot
if not exist "%MLOS_ROOT%\scripts\init.windows.cmd" (
    echo ERROR: MLOS_ROOT=%MLOS_ROOT% does not exist or is invalid.
    goto error
)
rem else ...
goto MlosRootIsSet

:SetMlosRoot
echo MLOS_ROOT environment variable was not set.  Defaulting to current directory.
pushd "%~dp0\.."
set "MLOS_ROOT=%CD%"
popd

:MlosRootIsSet
echo MLOS_ROOT=%MLOS_ROOT%

rem For now, assume amd64 as our target architecture.
set VsArch=amd64

set DOTNET_CLI_TELEMETRY_OPTOUT=1

rem Find an appropriate VS (2019) install to setup the environment.
set VsDevCmdPath=
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\Common7\Tools\VsDevCmd.bat" goto Vs2019Enterprise
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\Common7\Tools\VsDevCmd.bat" goto Vs2019Community
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\Tools\VsDevCmd.bat" goto Vs2019BuildTools
rem else ...
echo ERROR: Couldn't find VsDevCmd.bat.  Please check that you're installed the necessary prerequisites.
goto error

:Vs2019Enterprise
set "VsDevCmdPath=C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\Common7\Tools\VsDevCmd.bat"
goto VsDevCmdReady

:Vs2019Community
set "VsDevCmdPath=C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\Common7\Tools\VsDevCmd.bat"
goto VsDevCmdReady

:Vs2019BuildTools
set "VsDevCmdPath=C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\Tools\VsDevCmd.bat"
goto VsDevCmdReady

:VsDevCmdReady
call "%VsDevCmdPath%" -arch=%VsArch% >nul

rem Setup the default target platform to build for.
if "%VsArch%" neq "amd64" (
    echo Unhandled VsArch: %VsArch%
    goto error
)
rem This causes issues when also running the cake based build.
rem if "%Platform%" == "" set Platform=x64
rem if "%Platform%" neq "x64" (
rem     echo Unhandled Platform: %Platform%
rem     goto error
rem )
goto eof

:error
rem set ERRORLEVEL=1
exit /b 1

:eof
rem Cleanup our variables from the environment.
set VsArch=
set VsDevCmdPath=
rem Done
