rem Move to the root of the repo.
pushd "%~dp0\.."

rem Setup the build environment.
call .\scripts\init.windows.cmd

echo on

nuget sources -Verbosity detailed -Format Detailed
dotnet nuget list source --format Detailed

popd
