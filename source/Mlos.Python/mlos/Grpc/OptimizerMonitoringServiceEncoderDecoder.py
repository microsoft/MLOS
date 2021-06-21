#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#

from typing import Union

from mlos.Grpc import OptimizerMonitoringService_pb2
from mlos.Optimizers.OptimizationProblem import Objective, OptimizationProblem
from mlos.Spaces import CategoricalDimension, CompositeDimension, ContinuousDimension, Dimension, DiscreteDimension, \
    EmptyDimension, OrdinalDimension, SimpleHypergrid


class OptimizerMonitoringServiceEncoder:

    dimension_types_to_pb2_types = {
        CategoricalDimension: OptimizerMonitoringService_pb2.DimensionType.CATEGORICAL,
        ContinuousDimension: OptimizerMonitoringService_pb2.DimensionType.CONTINUOUS,
        DiscreteDimension: OptimizerMonitoringService_pb2.DimensionType.DISCRETE,
        OrdinalDimension: OptimizerMonitoringService_pb2.DimensionType.ORDINAL
    }

    """Encodes objects to the format expected by the OptimizerMonitoringService.
    """
    @staticmethod
    def encode_hypergrid(hypergrid: SimpleHypergrid) -> OptimizerMonitoringService_pb2.SimpleHypergrid:
        assert isinstance(hypergrid, SimpleHypergrid)
        encoded_subgrids = []
        for _, subgrids in hypergrid.joined_subgrids_by_pivot_dimension.items():
            for subgrid in subgrids:
                encoded_subgrid = OptimizerMonitoringServiceEncoder.encode_subgrid(subgrid)
                encoded_subgrids.append(encoded_subgrid)

        return OptimizerMonitoringService_pb2.SimpleHypergrid(
            Name=hypergrid.name,
            Dimensions=[OptimizerMonitoringServiceEncoder.encode_dimension(dimension) for dimension in hypergrid.root_dimensions],
            GuestSubgrids=encoded_subgrids
        )

    @staticmethod
    def encode_optimization_problem(optimization_problem: OptimizationProblem) -> OptimizerMonitoringService_pb2.OptimizationProblem:
        return OptimizerMonitoringService_pb2.OptimizationProblem(
            ParameterSpace=OptimizerMonitoringServiceEncoder.encode_hypergrid(optimization_problem.parameter_space),
            ObjectiveSpace=OptimizerMonitoringServiceEncoder.encode_hypergrid(optimization_problem.objective_space),
            Objectives=[OptimizerMonitoringService_pb2.Objective(Name=objective.name, Minimize=objective.minimize)
                        for objective in optimization_problem.objectives],
            ContextSpace=None if optimization_problem.context_space is None else
            OptimizerMonitoringServiceEncoder.encode_hypergrid(optimization_problem.context_space)
        )

    @staticmethod
    def encode_continuous_dimension(dimension: ContinuousDimension) -> OptimizerMonitoringService_pb2.ContinuousDimension:
        assert isinstance(dimension, ContinuousDimension)
        return OptimizerMonitoringService_pb2.ContinuousDimension(
            Name=dimension.name,
            Min=dimension.min,
            Max=dimension.max,
            IncludeMin=dimension.include_min,
            IncludeMax=dimension.include_max
        )

    @staticmethod
    def encode_discrete_dimension(dimension: DiscreteDimension) -> OptimizerMonitoringService_pb2.DiscreteDimension:
        assert isinstance(dimension, DiscreteDimension)
        return OptimizerMonitoringService_pb2.DiscreteDimension(Name=dimension.name, Min=dimension.min, Max=dimension.max)

    @staticmethod
    def encode_empty_dimension(dimension: EmptyDimension) -> OptimizerMonitoringService_pb2.EmptyDimension:
        assert isinstance(dimension, EmptyDimension)
        return OptimizerMonitoringService_pb2.EmptyDimension(
            Name=dimension.name,
            DimensionType=OptimizerMonitoringServiceEncoder.dimension_types_to_pb2_types[dimension.type]
        )

    @staticmethod
    def encode_categorical_dimension(dimension: CategoricalDimension) -> OptimizerMonitoringService_pb2.CategoricalDimension:
        assert isinstance(dimension, CategoricalDimension)
        return OptimizerMonitoringService_pb2.CategoricalDimension(
            Name=dimension.name,
            Values=[OptimizerMonitoringServiceEncoder.encode_primitive_value(value) for value in dimension.values]
        )

    @staticmethod
    def encode_ordinal_dimension(dimension: OrdinalDimension) -> OptimizerMonitoringService_pb2.OrdinalDimension:
        assert isinstance(dimension, OrdinalDimension)
        return OptimizerMonitoringService_pb2.OrdinalDimension(
            Name=dimension.name,
            Ascending=dimension.ascending,
            OrderedValues=[OptimizerMonitoringServiceEncoder.encode_primitive_value(value) for value in dimension.values]
        )

    @staticmethod
    def encode_composite_dimension(dimension: CompositeDimension) -> OptimizerMonitoringService_pb2.CompositeDimension:
        assert isinstance(dimension, CompositeDimension)

        encoded_chunks = []
        for chunk in dimension.enumerate_chunks():
            if dimension.chunks_type is ContinuousDimension:
                encoded_chunks.append(OptimizerMonitoringService_pb2.Dimension(
                    ContinuousDimension=OptimizerMonitoringServiceEncoder.encode_continuous_dimension(chunk)))
            elif dimension.chunks_type is DiscreteDimension:
                encoded_chunks.append(OptimizerMonitoringService_pb2.Dimension(
                    DiscreteDimension=OptimizerMonitoringServiceEncoder.encode_discrete_dimension(chunk)))
            elif dimension.chunks_type is OrdinalDimension:
                encoded_chunks.append(OptimizerMonitoringService_pb2.Dimension(
                    OrdinalDimension=OptimizerMonitoringServiceEncoder.encode_ordinal_dimension(chunk)))
            elif dimension.chunks_type is CategoricalDimension:
                encoded_chunks.append(
                    OptimizerMonitoringService_pb2.Dimension(CategoricalDimension=OptimizerMonitoringServiceEncoder.encode_categorical_dimension(chunk))
                )
            else:
                raise TypeError(f"Unsupported chunk type: {dimension.chunks_type.__name__}")

        return OptimizerMonitoringService_pb2.CompositeDimension(
            Name=dimension.name,
            ChunkType=OptimizerMonitoringServiceEncoder.dimension_types_to_pb2_types[dimension.chunks_type],
            Chunks=encoded_chunks
        )

    @staticmethod
    def encode_dimension(dimension: Dimension) -> OptimizerMonitoringService_pb2.Dimension:
        if isinstance(dimension, EmptyDimension):
            return OptimizerMonitoringService_pb2.Dimension(
                EmptyDimension=OptimizerMonitoringServiceEncoder.encode_empty_dimension(dimension))

        if isinstance(dimension, ContinuousDimension):
            return OptimizerMonitoringService_pb2.Dimension(
                ContinuousDimension=OptimizerMonitoringServiceEncoder.encode_continuous_dimension(dimension))

        if isinstance(dimension, DiscreteDimension):
            return OptimizerMonitoringService_pb2.Dimension(
                DiscreteDimension=OptimizerMonitoringServiceEncoder.encode_discrete_dimension(dimension))

        if isinstance(dimension, OrdinalDimension):
            return OptimizerMonitoringService_pb2.Dimension(
                OrdinalDimension=OptimizerMonitoringServiceEncoder.encode_ordinal_dimension(dimension))

        if isinstance(dimension, CategoricalDimension):
            return OptimizerMonitoringService_pb2.Dimension(
                CategoricalDimension=OptimizerMonitoringServiceEncoder.encode_categorical_dimension(dimension))

        if isinstance(dimension, CompositeDimension):
            return OptimizerMonitoringService_pb2.Dimension(
                CompositeDimension=OptimizerMonitoringServiceEncoder.encode_composite_dimension(dimension))

        raise TypeError(f"Unsupported dimension type: {type(dimension)}")

    @staticmethod
    def encode_subgrid(subgrid: SimpleHypergrid.JoinedSubgrid) -> OptimizerMonitoringService_pb2.GuestSubgrid:
        assert isinstance(subgrid, SimpleHypergrid.JoinedSubgrid)
        return OptimizerMonitoringService_pb2.GuestSubgrid(
            Subgrid=OptimizerMonitoringServiceEncoder.encode_hypergrid(subgrid.subgrid),
            ExternalPivotDimension=OptimizerMonitoringServiceEncoder.encode_dimension(subgrid.join_dimension)
        )

    @staticmethod
    def encode_primitive_value(value: Union[int, float, bool, str]) -> OptimizerMonitoringService_pb2.PrimitiveValue:
        assert isinstance(value, (int, float, bool, str))
        if isinstance(value, bool):
            return OptimizerMonitoringService_pb2.PrimitiveValue(BoolValue=value)
        if isinstance(value, int):
            return OptimizerMonitoringService_pb2.PrimitiveValue(IntValue=value)
        if isinstance(value, float):
            return OptimizerMonitoringService_pb2.PrimitiveValue(DoubleValue=value)
        if isinstance(value, str):
            return OptimizerMonitoringService_pb2.PrimitiveValue(StringValue=value)

        raise TypeError(f"{value} is of type: {type(value)} but must be one of (int, float, bool, str)")


class OptimizerMonitoringServiceDecoder:
    """Decodes OptimizerMonitoringService messages to objects.
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

    pb2_dimension_types_to_dimension_types = {
        OptimizerMonitoringService_pb2.DimensionType.CATEGORICAL: CategoricalDimension,
        OptimizerMonitoringService_pb2.DimensionType.CONTINUOUS: ContinuousDimension,
        OptimizerMonitoringService_pb2.DimensionType.DISCRETE: DiscreteDimension,
        OptimizerMonitoringService_pb2.DimensionType.ORDINAL: OrdinalDimension
    }

    @staticmethod
    def decode_optimization_problem(optimization_problem_pb2: OptimizerMonitoringService_pb2.OptimizationProblem) -> OptimizationProblem:
        return OptimizationProblem(
            parameter_space=OptimizerMonitoringServiceDecoder.decode_hypergrid(optimization_problem_pb2.ParameterSpace),
            objective_space=OptimizerMonitoringServiceDecoder.decode_hypergrid(optimization_problem_pb2.ObjectiveSpace),
            objectives=[
                Objective(name=objective_pb2.Name, minimize=objective_pb2.Minimize)
                for objective_pb2 in optimization_problem_pb2.Objectives
            ],
            context_space=None if not optimization_problem_pb2.HasField("ContextSpace") else
            OptimizerMonitoringServiceDecoder.decode_hypergrid(optimization_problem_pb2.ContextSpace)
        )

    @staticmethod
    def decode_continuous_dimension(serialized: OptimizerMonitoringService_pb2.ContinuousDimension) -> ContinuousDimension:
        assert isinstance(serialized, OptimizerMonitoringService_pb2.ContinuousDimension)
        return ContinuousDimension(
            name=serialized.Name,
            min=serialized.Min,
            max=serialized.Max,
            include_min=serialized.IncludeMin,
            include_max=serialized.IncludeMax
        )

    @staticmethod
    def decode_discrete_dimension(serialized: OptimizerMonitoringService_pb2.DiscreteDimension) -> DiscreteDimension:
        assert isinstance(serialized, OptimizerMonitoringService_pb2.DiscreteDimension)
        return DiscreteDimension(name=serialized.Name, min=serialized.Min, max=serialized.Max)

    @staticmethod
    def decode_empty_dimension(serialized: OptimizerMonitoringService_pb2.EmptyDimension) -> EmptyDimension:
        assert isinstance(serialized, OptimizerMonitoringService_pb2.EmptyDimension)
        return EmptyDimension(
            name=serialized.Name,
            type=OptimizerMonitoringServiceDecoder.pb2_dimension_types_to_dimension_types[serialized.DimensionType]
        )

    @staticmethod
    def decode_categorical_dimension(serialized: OptimizerMonitoringService_pb2.CategoricalDimension) -> CategoricalDimension:
        assert isinstance(serialized, OptimizerMonitoringService_pb2.CategoricalDimension)
        return CategoricalDimension(
            name=serialized.Name,
            values=[OptimizerMonitoringServiceDecoder.decode_primitive_value(value) for value in serialized.Values]
        )

    @staticmethod
    def decode_ordinal_dimension(serialized: OptimizerMonitoringService_pb2.OrdinalDimension) -> OrdinalDimension:
        assert isinstance(serialized, OptimizerMonitoringService_pb2.OrdinalDimension)
        return OrdinalDimension(
            name=serialized.Name,
            ascending=serialized.Ascending,
            ordered_values=[OptimizerMonitoringServiceDecoder.decode_primitive_value(value) for value in serialized.OrderedValues]
        )

    @staticmethod
    def decode_composite_dimension(serialized: OptimizerMonitoringService_pb2.CompositeDimension) -> CompositeDimension:
        assert isinstance(serialized, OptimizerMonitoringService_pb2.CompositeDimension)

        if serialized.ChunkType == OptimizerMonitoringService_pb2.DimensionType.CONTINUOUS:
            decoded_chunks = [OptimizerMonitoringServiceDecoder.decode_continuous_dimension(chunk.ContinuousDimension)
                              for chunk in serialized.Chunks]
        elif serialized.ChunkType == OptimizerMonitoringService_pb2.DimensionType.DISCRETE:
            decoded_chunks = [OptimizerMonitoringServiceDecoder.decode_discrete_dimension(chunk.DiscreteDimension)
                              for chunk in serialized.Chunks]
        elif serialized.ChunkType == OptimizerMonitoringService_pb2.DimensionType.ORDINAL:
            decoded_chunks = [OptimizerMonitoringServiceDecoder.decode_ordinal_dimension(chunk.OrdinalDimension)
                              for chunk in serialized.Chunks]
        elif serialized.ChunkType == OptimizerMonitoringService_pb2.DimensionType.CATEGORICAL:
            decoded_chunks = [OptimizerMonitoringServiceDecoder.decode_categorical_dimension(chunk.CategoricalDimension)
                              for chunk in serialized.Chunks]
        else:
            raise TypeError(f"Unsupported chunk type: {serialized.ChunkType}")

        return CompositeDimension(
            name=serialized.Name,
            chunks_type=OptimizerMonitoringServiceDecoder.pb2_dimension_types_to_dimension_types[serialized.ChunkType],
            chunks=decoded_chunks
        )

    @staticmethod
    def decode_hypergrid(hypergrid: OptimizerMonitoringService_pb2.SimpleHypergrid) -> SimpleHypergrid:
        assert isinstance(hypergrid, OptimizerMonitoringService_pb2.SimpleHypergrid)
        decoded_hypergrid = SimpleHypergrid(
            name=hypergrid.Name,
            dimensions=[OptimizerMonitoringServiceDecoder.decode_dimension(dimension) for dimension in hypergrid.Dimensions]
        )

        for subgrid in hypergrid.GuestSubgrids:
            decoded_subgrid = OptimizerMonitoringServiceDecoder.decode_subgrid(subgrid)
            decoded_hypergrid.join(
                subgrid=decoded_subgrid.subgrid,
                on_external_dimension=decoded_subgrid.join_dimension
            )

        return decoded_hypergrid

    @staticmethod
    def decode_dimension(dimension: OptimizerMonitoringService_pb2.Dimension) -> Dimension:
        assert isinstance(dimension, OptimizerMonitoringService_pb2.Dimension)
        dimension_type_set = dimension.WhichOneof('Dimension')
        supported_dimension_types = [CategoricalDimension, CompositeDimension, ContinuousDimension, EmptyDimension,
                                     DiscreteDimension, OrdinalDimension]
        supported_dimension_type_names = [type_.__name__ for type_ in supported_dimension_types]
        assert dimension_type_set in supported_dimension_type_names

        if dimension_type_set == CategoricalDimension.__name__:
            return OptimizerMonitoringServiceDecoder.decode_categorical_dimension(dimension.CategoricalDimension)

        if dimension_type_set == CompositeDimension.__name__:
            return OptimizerMonitoringServiceDecoder.decode_composite_dimension(dimension.CompositeDimension)

        if dimension_type_set == ContinuousDimension.__name__:
            return OptimizerMonitoringServiceDecoder.decode_continuous_dimension(dimension.ContinuousDimension)

        if dimension_type_set == EmptyDimension.__name__:
            return OptimizerMonitoringServiceDecoder.decode_empty_dimension(dimension.EmptyDimension)

        if dimension_type_set == DiscreteDimension.__name__:
            return OptimizerMonitoringServiceDecoder.decode_discrete_dimension(dimension.DiscreteDimension)

        if dimension_type_set == OrdinalDimension.__name__:
            return OptimizerMonitoringServiceDecoder.decode_ordinal_dimension(dimension.OrdinalDimension)

        raise TypeError(f"Unsupported dimension type: {dimension_type_set}")

    @staticmethod
    def decode_subgrid(subgrid: OptimizerMonitoringService_pb2.GuestSubgrid) -> SimpleHypergrid.JoinedSubgrid:
        assert isinstance(subgrid, OptimizerMonitoringService_pb2.GuestSubgrid)
        return SimpleHypergrid.JoinedSubgrid(
            subgrid=OptimizerMonitoringServiceDecoder.decode_hypergrid(subgrid.Subgrid),
            join_dimension=OptimizerMonitoringServiceDecoder.decode_dimension(subgrid.ExternalPivotDimension)
        )

    @staticmethod
    def decode_primitive_value(value: OptimizerMonitoringService_pb2.PrimitiveValue) -> Union[int, float, bool, str]:
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

        raise TypeError(f"Unsupported field was set: {field_set}")
