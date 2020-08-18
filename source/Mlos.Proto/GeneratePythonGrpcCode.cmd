:: Copyright (c) Microsoft Corporation.
:: Licensed under the MIT License.

@echo off
rem We need to recreate the structure of the python module in the input to grpc
rem to have the imports be generated correctly. See https://github.com/grpc/grpc/issues/9575#issuecomment-293934506
mkdir mlos\Grpc
copy OptimizerService.proto mlos\Grpc\
python -m grpc_tools.protoc -I . --python_out=..\Mlos.Python --grpc_python_out=..\Mlos.Python  mlos\Grpc\OptimizerService.proto
rd /s /q mlos
