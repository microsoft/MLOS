# pylint: disable=import-error,wrong-import-position
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import os
import sys

# This is the directory where the grpc outputs generated code.
#
grpc_dir = os.path.abspath(os.path.join(os.getcwd(), "Grpc"))
sys.path.insert(0, grpc_dir)

from . import OptimizerService_pb2
from . import OptimizerService_pb2_grpc

__all__ = [
    "OptimizerService_pb2",
    "OptimizerService_pb2_grpc"
]

# Make sure there are no http_proxy environment variables set.
# See Also: https://stackoverflow.com/a/57868784/10772564
if os.environ.get('https_proxy'):
    del os.environ['https_proxy']
if os.environ.get('http_proxy'):
    del os.environ['http_proxy']
