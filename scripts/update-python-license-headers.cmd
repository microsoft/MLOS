:: Copyright (c) Microsoft Corporation.
:: Licensed under the MIT License.

@echo off
rem Update the license headers for Python files.

rem Start at the root of the repo.
pushd "%~dp0\.."

cd source\Mlos.Python
licenseheaders -t mit-license.tmpl -E .py -x mlos\Grpc\OptimizerService_pb2_grpc.py mlos\Grpc\OptimizerService_pb2.py

popd
@echo on
exit /B %ERRORLEVEL%
