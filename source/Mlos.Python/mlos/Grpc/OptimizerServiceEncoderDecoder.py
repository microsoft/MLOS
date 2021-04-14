#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json

from mlos.Grpc import OptimizerService_pb2
from mlos.Optimizers.OptimizationProblem import Objective, OptimizationProblem
from mlos.Spaces import CategoricalDimension, CompositeDimension, ContinuousDimension, DiscreteDimension, EmptyDimension, OrdinalDimension
from mlos.Spaces.HypergridsJsonEncoderDecoder import HypergridJsonDecoder, HypergridJsonEncoder


class OptimizerServiceEncoder:
    """Encodes objects to the format expected by the OptimizerService.
    """
    @staticmethod
    def encode_optimization_problem(optimization_problem: OptimizationProblem) -> OptimizerService_pb2.OptimizationProblem:
        return OptimizerService_pb2.OptimizationProblem(
            ParameterSpace=OptimizerService_pb2.Hypergrid(HypergridJsonString=json.dumps(optimization_problem.parameter_space, cls=HypergridJsonEncoder)),
            ObjectiveSpace=OptimizerService_pb2.Hypergrid(HypergridJsonString=json.dumps(optimization_problem.objective_space, cls=HypergridJsonEncoder)),
            Objectives=[OptimizerService_pb2.Objective(Name=objective.name, Minimize=objective.minimize) for objective in optimization_problem.objectives],
            ContextSpace=None if optimization_problem.context_space is None
            else OptimizerService_pb2.Hypergrid(HypergridJsonString=json.dumps(optimization_problem.context_space, cls=HypergridJsonEncoder))
        )

    @staticmethod
    def encode_empty_dimension(empty_dimension: EmptyDimension):
        assert isinstance(empty_dimension, EmptyDimension)
        return OptimizerService_pb2.EmptyDimension(
            Name=empty_dimension.name,
            Type=empty_dimension.type.__name__
        )

class OptimizerServiceDecoder:
    """Decodes OptimizerService messages to objects.
    """
    type_names_to_types = {
        dimension_type.__name__: dimension_type
        for dimension_type
        in [
            EmptyDimension,
            CategoricalDimension,
            ContinuousDimension,
            DiscreteDimension,
            OrdinalDimension,
            CompositeDimension
        ]
    }

    @staticmethod
    def decode_optimization_problem(optimization_problem_pb2: OptimizerService_pb2.OptimizationProblem) -> OptimizationProblem:
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

    @staticmethod
    def decode_empty_dimension(serialized: OptimizerService_pb2.EmptyDimension):
        assert isinstance(serialized, OptimizerService_pb2.EmptyDimension)
        return EmptyDimension(
            name=serialized.Name,
            type=OptimizerServiceDecoder.type_names_to_types[serialized.Type]
        )
