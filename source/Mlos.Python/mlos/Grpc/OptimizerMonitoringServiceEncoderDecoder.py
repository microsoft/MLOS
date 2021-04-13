#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json

from mlos.Grpc.OptimizerMonitoringService_pb2 import Hypergrid, OptimizationProblem as OptimizationProblem_pb2, Objective as Objective_pb2
from mlos.Optimizers.OptimizationProblem import Objective, OptimizationProblem
from mlos.Spaces.HypergridsJsonEncoderDecoder import HypergridJsonDecoder, HypergridJsonEncoder


class OptimizerMonitoringServiceEncoder:
    """Encodes objects to the format expected by the OptimizerService.
    """

    @staticmethod
    def encode_optimization_problem(optimization_problem: OptimizationProblem) -> OptimizationProblem_pb2:
        return OptimizationProblem_pb2(
            ParameterSpace=Hypergrid(HypergridJsonString=json.dumps(optimization_problem.parameter_space, cls=HypergridJsonEncoder)),
            ObjectiveSpace=Hypergrid(HypergridJsonString=json.dumps(optimization_problem.objective_space, cls=HypergridJsonEncoder)),
            Objectives=[Objective_pb2(Name=objective.name, Minimize=objective.minimize) for objective in optimization_problem.objectives],
            ContextSpace=None if optimization_problem.context_space is None
            else Hypergrid(HypergridJsonString=json.dumps(optimization_problem.context_space, cls=HypergridJsonEncoder))
        )


class OptimizerMonitoringServiceDecoder:
    """Decodes OptimizerService messages to objects.
    """

    @staticmethod
    def decode_optimization_problem(optimization_problem_pb2: OptimizationProblem_pb2) -> OptimizationProblem:
        return OptimizationProblem(
            parameter_space=json.loads(optimization_problem_pb2.ParameterSpace.HypergridJsonString, cls=HypergridJsonDecoder),
            objective_space=json.loads(optimization_problem_pb2.ObjectiveSpace.HypergridJsonString, cls=HypergridJsonDecoder),
            objectives=[
                Objective(name=objective_pb2.Name, minimize=objective_pb2.Minimize)
                for objective_pb2 in optimization_problem_pb2.Objectives
            ],
            context_space=None if not optimization_problem_pb2.ContextSpace.HypergridJsonString
            else json.loads(optimization_problem_pb2.ContextSpace.HypergridJsonString, cls=HypergridJsonDecoder)
        )
