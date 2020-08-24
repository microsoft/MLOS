#!/bin/bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# Update the license headers for Python files.

set -eu

# Start at the root of the repo.
scriptdir=$(readlink -f "$(dirname "$0")")
cd "$scriptdir/.."

cd source/Mlos.Python
licenseheaders -t mit-license.tmpl -E .py -x mlos/Grpc/OptimizerService_pb2_grpc.py mlos/Grpc/OptimizerService_pb2.py
