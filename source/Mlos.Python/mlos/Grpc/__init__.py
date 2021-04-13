# pylint: disable=import-error,wrong-import-position
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import os
import sys
import warnings

# This is the directory where the grpc outputs generated code.
#
grpc_dir = os.path.abspath(os.path.join(os.getcwd(), "Grpc"))
sys.path.insert(0, grpc_dir)

from . import OptimizerService_pb2
from . import OptimizerService_pb2_grpc
from . import OptimizerMonitoringService_pb2
from . import OptimizerMonitoringService_pb2_grpc

__all__ = [
    "OptimizerMonitoringService_pb2",
    "OptimizerMonitoringService_pb2_grpc",
    "OptimizerService_pb2",
    "OptimizerService_pb2_grpc",
]

# Make sure there are no http_proxy environment variables set.
# See Also: https://stackoverflow.com/a/57868784/10772564
if os.environ.get('https_proxy'):
    warnings.warn("Use of https_proxy environment variable may cause issues with Grpc.")
if os.environ.get('http_proxy'):
    warnings.warn("Use of http_proxy environment variable may cause issues with Grpc.")
