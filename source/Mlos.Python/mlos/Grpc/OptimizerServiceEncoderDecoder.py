#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json
from typing import Union

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
    def encode_empty_dimension(dimension: EmptyDimension) -> OptimizerService_pb2.EmptyDimension:
        assert isinstance(dimension, EmptyDimension)
        return OptimizerService_pb2.EmptyDimension(Name=dimension.name, Type=dimension.type.__name__)

    @staticmethod
    def encode_categorical_dimension(dimension: CategoricalDimension) -> OptimizerService_pb2.CategoricalDimension:
        assert isinstance(dimension, CategoricalDimension)
        return OptimizerService_pb2.CategoricalDimension(
            Name=dimension.name,
            Values=[OptimizerServiceEncoder.encode_primitive_value(value) for value in dimension.values]
        )

    @staticmethod
    def encode_ordinal_dimension(dimension: OrdinalDimension) -> OptimizerService_pb2.OrdinalDimension:
        assert isinstance(dimension, OrdinalDimension)
        return OptimizerService_pb2.OrdinalDimension(
            Name=dimension.name,
            Ascending=dimension.ascending,
            OrderedValues=[OptimizerServiceEncoder.encode_primitive_value(value) for value in dimension.values]
        )

    @staticmethod
    def encode_primitive_value(value: Union[int, float, bool, str]) -> OptimizerService_pb2.PrimitiveValue:
        assert isinstance(value, (int, float, bool, str))
        if isinstance(value, bool):
            return OptimizerService_pb2.PrimitiveValue(BoolValue=value)
        if isinstance(value, int):
            return OptimizerService_pb2.PrimitiveValue(IntValue=value)
        if isinstance(value, float):
            return OptimizerService_pb2.PrimitiveValue(DoubleValue=value)
        if isinstance(value, str):
            return OptimizerService_pb2.PrimitiveValue(StringValue=value)

        raise TypeError(f"{value} is of type: {type(value)} but must be one of (int, float, bool, str)")

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
    def decode_empty_dimension(serialized: OptimizerService_pb2.EmptyDimension) -> EmptyDimension:
        assert isinstance(serialized, OptimizerService_pb2.EmptyDimension)
        return EmptyDimension(
            name=serialized.Name,
            type=OptimizerServiceDecoder.type_names_to_types[serialized.Type]
        )

    @staticmethod
    def decode_categorical_dimension(serialized: OptimizerService_pb2.CategoricalDimension) -> CategoricalDimension:
        assert isinstance(serialized, OptimizerService_pb2.CategoricalDimension)
        return CategoricalDimension(
            name=serialized.Name,
            values=[OptimizerServiceDecoder.decode_primitive_value(value) for value in serialized.Values]
        )

    @staticmethod
    def decode_ordinal_dimension(serialized: OptimizerService_pb2.OrdinalDimension) -> OrdinalDimension:
        assert isinstance(serialized, OptimizerService_pb2.OrdinalDimension)
        return OrdinalDimension(
            name=serialized.Name,
            ascending=serialized.Ascending,
            ordered_values=[OptimizerServiceDecoder.decode_primitive_value(value) for value in serialized.OrderedValues]
        )

    @staticmethod
    def decode_primitive_value(value: OptimizerService_pb2.PrimitiveValue) -> Union[int, float, bool, str]:
        field_set = value.WhichOneof('Value')
        assert field_set in ('IntValue', 'DoubleValue', 'BoolValue', 'StringValue')
        if field_set == 'IntValue':
            return value.IntValue
        if field_set == 'DoubleValue':
            return value.DoubleValue
        if field_set == "BoolValue":
            return value.BoolValue
        if field_set == "StringValue":
            return value.StringValue
