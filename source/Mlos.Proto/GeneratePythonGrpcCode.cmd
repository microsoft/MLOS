:: Copyright (c) Microsoft Corporation.
:: Licensed under the MIT License.

@echo off
rem We need to recreate the structure of the python module in the input to grpc
rem to have the imports be generated correctly. See https://github.com/grpc/grpc/issues/9575#issuecomment-293934506

rem Start in the script directory.
pushd "%~dp0"

mkdir mlos\Grpc

copy OptimizerService.proto mlos\Grpc\
python -m grpc_tools.protoc -I . --python_out=..\Mlos.Python --grpc_python_out=..\Mlos.Python  mlos/Grpc/OptimizerService.proto

copy OptimizerMonitoringService.proto mlos\Grpc\
python -m grpc_tools.protoc -I . --python_out=..\Mlos.Python --grpc_python_out=..\Mlos.Python  mlos/Grpc/OptimizerMonitoringService.proto

rem rd /s /q mlos

popd
@echo on
