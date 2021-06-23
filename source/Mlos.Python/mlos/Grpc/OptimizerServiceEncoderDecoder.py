#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#

from typing import Union

from mlos.Grpc import OptimizerService_pb2
from mlos.Optimizers.OptimizationProblem import Objective, OptimizationProblem
from mlos.Spaces import CategoricalDimension, CompositeDimension, ContinuousDimension, Dimension, DiscreteDimension, \
    EmptyDimension, OrdinalDimension, SimpleHypergrid


class OptimizerServiceEncoder:

    dimension_types_to_pb2_types = {
        CategoricalDimension: OptimizerService_pb2.DimensionType.CATEGORICAL,
        ContinuousDimension: OptimizerService_pb2.DimensionType.CONTINUOUS,
        DiscreteDimension: OptimizerService_pb2.DimensionType.DISCRETE,
        OrdinalDimension: OptimizerService_pb2.DimensionType.ORDINAL
    }

    """Encodes objects to the format expected by the OptimizerService.
    """
    @staticmethod
    def encode_hypergrid(hypergrid: SimpleHypergrid) -> OptimizerService_pb2.SimpleHypergrid:
        assert isinstance(hypergrid, SimpleHypergrid)
        encoded_subgrids = []
        for _, subgrids in hypergrid.joined_subgrids_by_pivot_dimension.items():
            for subgrid in subgrids:
                encoded_subgrid = OptimizerServiceEncoder.encode_subgrid(subgrid)
                encoded_subgrids.append(encoded_subgrid)

        return OptimizerService_pb2.SimpleHypergrid(
            Name=hypergrid.name,
            Dimensions=[OptimizerServiceEncoder.encode_dimension(dimension) for dimension in hypergrid.root_dimensions],
            GuestSubgrids=encoded_subgrids
        )

    @staticmethod
    def encode_optimization_problem(optimization_problem: OptimizationProblem) -> OptimizerService_pb2.OptimizationProblem:
        return OptimizerService_pb2.OptimizationProblem(
            ParameterSpace=OptimizerServiceEncoder.encode_hypergrid(optimization_problem.parameter_space),
            ObjectiveSpace=OptimizerServiceEncoder.encode_hypergrid(optimization_problem.objective_space),
            Objectives=[OptimizerService_pb2.Objective(Name=objective.name, Minimize=objective.minimize)
                        for objective in optimization_problem.objectives],
            ContextSpace=None if optimization_problem.context_space is None else
            OptimizerServiceEncoder.encode_hypergrid(optimization_problem.context_space)
        )

    @staticmethod
    def encode_continuous_dimension(dimension: ContinuousDimension) -> OptimizerService_pb2.ContinuousDimension:
        assert isinstance(dimension, ContinuousDimension)
        return OptimizerService_pb2.ContinuousDimension(
            Name=dimension.name,
            Min=dimension.min,
            Max=dimension.max,
            IncludeMin=dimension.include_min,
            IncludeMax=dimension.include_max
        )

    @staticmethod
    def encode_discrete_dimension(dimension: DiscreteDimension) -> OptimizerService_pb2.DiscreteDimension:
        assert isinstance(dimension, DiscreteDimension)
        return OptimizerService_pb2.DiscreteDimension(Name=dimension.name, Min=dimension.min, Max=dimension.max)

    @staticmethod
    def encode_empty_dimension(dimension: EmptyDimension) -> OptimizerService_pb2.EmptyDimension:
        assert isinstance(dimension, EmptyDimension)
        return OptimizerService_pb2.EmptyDimension(
            Name=dimension.name,
            DimensionType=OptimizerServiceEncoder.dimension_types_to_pb2_types[dimension.type]
        )

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
    def encode_composite_dimension(dimension: CompositeDimension) -> OptimizerService_pb2.CompositeDimension:
        assert isinstance(dimension, CompositeDimension)

        encoded_chunks = []
        for chunk in dimension.enumerate_chunks():
            if dimension.chunks_type is ContinuousDimension:
                encoded_chunks.append(OptimizerService_pb2.Dimension(
                    ContinuousDimension=OptimizerServiceEncoder.encode_continuous_dimension(chunk)))
            elif dimension.chunks_type is DiscreteDimension:
                encoded_chunks.append(OptimizerService_pb2.Dimension(
                    DiscreteDimension=OptimizerServiceEncoder.encode_discrete_dimension(chunk)))
            elif dimension.chunks_type is OrdinalDimension:
                encoded_chunks.append(OptimizerService_pb2.Dimension(
                    OrdinalDimension=OptimizerServiceEncoder.encode_ordinal_dimension(chunk)))
            elif dimension.chunks_type is CategoricalDimension:
                encoded_chunks.append(
                    OptimizerService_pb2.Dimension(CategoricalDimension=OptimizerServiceEncoder.encode_categorical_dimension(chunk))
                )
            else:
                raise TypeError(f"Unsupported chunk type: {dimension.chunks_type.__name__}")

        return OptimizerService_pb2.CompositeDimension(
            Name=dimension.name,
            ChunkType=OptimizerServiceEncoder.dimension_types_to_pb2_types[dimension.chunks_type],
            Chunks=encoded_chunks
        )

    @staticmethod
    def encode_dimension(dimension: Dimension) -> OptimizerService_pb2.Dimension:
        if isinstance(dimension, EmptyDimension):
            return OptimizerService_pb2.Dimension(
                EmptyDimension=OptimizerServiceEncoder.encode_empty_dimension(dimension))

        if isinstance(dimension, ContinuousDimension):
            return OptimizerService_pb2.Dimension(
                ContinuousDimension=OptimizerServiceEncoder.encode_continuous_dimension(dimension))

        if isinstance(dimension, DiscreteDimension):
            return OptimizerService_pb2.Dimension(
                DiscreteDimension=OptimizerServiceEncoder.encode_discrete_dimension(dimension))

        if isinstance(dimension, OrdinalDimension):
            return OptimizerService_pb2.Dimension(
                OrdinalDimension=OptimizerServiceEncoder.encode_ordinal_dimension(dimension))

        if isinstance(dimension, CategoricalDimension):
            return OptimizerService_pb2.Dimension(
                CategoricalDimension=OptimizerServiceEncoder.encode_categorical_dimension(dimension))

        if isinstance(dimension, CompositeDimension):
            return OptimizerService_pb2.Dimension(
                CompositeDimension=OptimizerServiceEncoder.encode_composite_dimension(dimension))

        raise TypeError(f"Unsupported dimension type: {type(dimension)}")

    @staticmethod
    def encode_subgrid(subgrid: SimpleHypergrid.JoinedSubgrid) -> OptimizerService_pb2.GuestSubgrid:
        assert isinstance(subgrid, SimpleHypergrid.JoinedSubgrid)
        return OptimizerService_pb2.GuestSubgrid(
            Subgrid=OptimizerServiceEncoder.encode_hypergrid(subgrid.subgrid),
            ExternalPivotDimension=OptimizerServiceEncoder.encode_dimension(subgrid.join_dimension)
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

    pb2_dimension_types_to_dimension_types = {
        OptimizerService_pb2.DimensionType.CATEGORICAL: CategoricalDimension,
        OptimizerService_pb2.DimensionType.CONTINUOUS: ContinuousDimension,
        OptimizerService_pb2.DimensionType.DISCRETE: DiscreteDimension,
        OptimizerService_pb2.DimensionType.ORDINAL: OrdinalDimension
    }

    @staticmethod
    def decode_hypergrid(hypergrid: OptimizerService_pb2.SimpleHypergrid) -> SimpleHypergrid:
        assert isinstance(hypergrid, OptimizerService_pb2.SimpleHypergrid)
        decoded_hypergrid = SimpleHypergrid(
            name=hypergrid.Name,
            dimensions=[OptimizerServiceDecoder.decode_dimension(dimension) for dimension in hypergrid.Dimensions]
        )

        for subgrid in hypergrid.GuestSubgrids:
            decoded_subgrid = OptimizerServiceDecoder.decode_subgrid(subgrid)
            decoded_hypergrid.join(
                subgrid=decoded_subgrid.subgrid,
                on_external_dimension=decoded_subgrid.join_dimension
            )

        return decoded_hypergrid

    @staticmethod
    def decode_optimization_problem(optimization_problem_pb2: OptimizerService_pb2.OptimizationProblem) -> OptimizationProblem:
        return OptimizationProblem(
            parameter_space=OptimizerServiceDecoder.decode_hypergrid(optimization_problem_pb2.ParameterSpace),
            objective_space=OptimizerServiceDecoder.decode_hypergrid(optimization_problem_pb2.ObjectiveSpace),
            objectives=[
                Objective(name=objective_pb2.Name, minimize=objective_pb2.Minimize)
                for objective_pb2 in optimization_problem_pb2.Objectives
            ],
            context_space=None if not optimization_problem_pb2.HasField("ContextSpace") else
            OptimizerServiceDecoder.decode_hypergrid(optimization_problem_pb2.ContextSpace)
        )

    @staticmethod
    def decode_continuous_dimension(serialized: OptimizerService_pb2.ContinuousDimension) -> ContinuousDimension:
        assert isinstance(serialized, OptimizerService_pb2.ContinuousDimension)
        return ContinuousDimension(
            name=serialized.Name,
            min=serialized.Min,
            max=serialized.Max,
            include_min=serialized.IncludeMin,
            include_max=serialized.IncludeMax
        )

    @staticmethod
    def decode_discrete_dimension(serialized: OptimizerService_pb2.DiscreteDimension) -> DiscreteDimension:
        assert isinstance(serialized, OptimizerService_pb2.DiscreteDimension)
        return DiscreteDimension(name=serialized.Name, min=serialized.Min, max=serialized.Max)

    @staticmethod
    def decode_empty_dimension(serialized: OptimizerService_pb2.EmptyDimension) -> EmptyDimension:
        assert isinstance(serialized, OptimizerService_pb2.EmptyDimension)
        return EmptyDimension(
            name=serialized.Name,
            type=OptimizerServiceDecoder.pb2_dimension_types_to_dimension_types[serialized.DimensionType]
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
    def decode_composite_dimension(serialized: OptimizerService_pb2.CompositeDimension) -> CompositeDimension:
        assert isinstance(serialized, OptimizerService_pb2.CompositeDimension)

        if serialized.ChunkType == OptimizerService_pb2.DimensionType.CONTINUOUS:
            decoded_chunks = [OptimizerServiceDecoder.decode_continuous_dimension(chunk.ContinuousDimension)
                              for chunk in serialized.Chunks]
        elif serialized.ChunkType == OptimizerService_pb2.DimensionType.DISCRETE:
            decoded_chunks = [OptimizerServiceDecoder.decode_discrete_dimension(chunk.DiscreteDimension)
                              for chunk in serialized.Chunks]
        elif serialized.ChunkType == OptimizerService_pb2.DimensionType.ORDINAL:
            decoded_chunks = [OptimizerServiceDecoder.decode_ordinal_dimension(chunk.OrdinalDimension)
                              for chunk in serialized.Chunks]
        elif serialized.ChunkType == OptimizerService_pb2.DimensionType.CATEGORICAL:
            decoded_chunks = [OptimizerServiceDecoder.decode_categorical_dimension(chunk.CategoricalDimension)
                              for chunk in serialized.Chunks]
        else:
            raise TypeError(f"Unsupported chunk type: {serialized.ChunkType}")

        return CompositeDimension(
            name=serialized.Name,
            chunks_type=OptimizerServiceDecoder.pb2_dimension_types_to_dimension_types[serialized.ChunkType],
            chunks=decoded_chunks
        )

    @staticmethod
    def decode_dimension(dimension: OptimizerService_pb2.Dimension) -> Dimension:
        assert isinstance(dimension, OptimizerService_pb2.Dimension)
        dimension_type_set = dimension.WhichOneof('Dimension')
        supported_dimension_types = [CategoricalDimension, CompositeDimension, ContinuousDimension, EmptyDimension,
                                     DiscreteDimension, OrdinalDimension]
        supported_dimension_type_names = [type_.__name__ for type_ in supported_dimension_types]
        assert dimension_type_set in supported_dimension_type_names

        if dimension_type_set == CategoricalDimension.__name__:
            return OptimizerServiceDecoder.decode_categorical_dimension(dimension.CategoricalDimension)

        if dimension_type_set == CompositeDimension.__name__:
            return OptimizerServiceDecoder.decode_composite_dimension(dimension.CompositeDimension)

        if dimension_type_set == ContinuousDimension.__name__:
            return OptimizerServiceDecoder.decode_continuous_dimension(dimension.ContinuousDimension)

        if dimension_type_set == EmptyDimension.__name__:
            return OptimizerServiceDecoder.decode_empty_dimension(dimension.EmptyDimension)

        if dimension_type_set == DiscreteDimension.__name__:
            return OptimizerServiceDecoder.decode_discrete_dimension(dimension.DiscreteDimension)

        if dimension_type_set == OrdinalDimension.__name__:
            return OptimizerServiceDecoder.decode_ordinal_dimension(dimension.OrdinalDimension)

        raise TypeError(f"Unsupported dimension type: {dimension_type_set}")

    @staticmethod
    def decode_subgrid(subgrid: OptimizerService_pb2.GuestSubgrid) -> SimpleHypergrid.JoinedSubgrid:
        assert isinstance(subgrid, OptimizerService_pb2.GuestSubgrid)
        return SimpleHypergrid.JoinedSubgrid(
            subgrid=OptimizerServiceDecoder.decode_hypergrid(subgrid.Subgrid),
            join_dimension=OptimizerServiceDecoder.decode_dimension(subgrid.ExternalPivotDimension)
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

        raise TypeError(f"Unsupported field was set: {field_set}")
