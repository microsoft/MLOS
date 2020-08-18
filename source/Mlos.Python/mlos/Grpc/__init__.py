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
