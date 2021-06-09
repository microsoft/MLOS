#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json


from mlos.Grpc import OptimizerShared_pb2
from mlos.Grpc import OptimizerMonitoringService_pb2

from mlos.Optimizers.OptimizationProblem import Objective, OptimizationProblem
from mlos.Grpc.OptimizerServiceEncoderDecoder import OptimizerServiceEncoder, OptimizerServiceDecoder

class OptimizerMonitoringServiceEncoder:
    """Encodes objects to the format expected by the OptimizerService.
    """

    @staticmethod
    def encode_optimization_problem(optimization_problem: OptimizationProblem) -> OptimizerShared_pb2.OptimizationProblem:
        return OptimizerServiceEncoder.encode_optimization_problem(optimization_problem)



class OptimizerMonitoringServiceDecoder:
    """Decodes OptimizerService messages to objects.
    """

    @staticmethod
    def decode_optimization_problem(optimization_problem_pb2: OptimizerShared_pb2.OptimizationProblem) -> OptimizationProblem:
        return OptimizerServiceDecoder.decode_optimization_problem(optimization_problem_pb2)
