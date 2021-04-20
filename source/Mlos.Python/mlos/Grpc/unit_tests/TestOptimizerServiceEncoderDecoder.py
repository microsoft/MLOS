#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pytest

from mlos.Grpc.OptimizerServiceEncoderDecoder import OptimizerServiceDecoder, OptimizerServiceEncoder
from mlos.Grpc import OptimizerService_pb2
from mlos.Spaces import CategoricalDimension, CompositeDimension, ContinuousDimension, DiscreteDimension, EmptyDimension, OrdinalDimension
from mlos.Optimizers.BayesianOptimizerConfigStore import bayesian_optimizer_config_store



class TestOptimizerServiceEncoderDecoder:
    """Tests encoding and decoding for dimensions.

    """

    def test_empty_dimension(self):
        empty_dimension = EmptyDimension(name="empty", type=ContinuousDimension)
        serialized = OptimizerServiceEncoder.encode_empty_dimension(empty_dimension)
        deserialized_empty_dimension = OptimizerServiceDecoder.decode_empty_dimension(serialized)

        assert isinstance(serialized, OptimizerService_pb2.EmptyDimension)
        assert empty_dimension == deserialized_empty_dimension

    def test_categorical_dimension(self):
        categorical_dimension = CategoricalDimension(name='categorical', values=[0, 1, True, False, "red", "green", "blue", 3.14, 7.5])
        serialized = OptimizerServiceEncoder.encode_categorical_dimension(categorical_dimension)
        deserialized_categorical_dimension = OptimizerServiceDecoder.decode_categorical_dimension(serialized)

        assert isinstance(serialized, OptimizerService_pb2.CategoricalDimension)
        assert categorical_dimension == deserialized_categorical_dimension

    @pytest.mark.parametrize('include_min', [True, False])
    @pytest.mark.parametrize('include_max', [True, False])
    def test_continuous_dimension(self, include_min, include_max):
        continuous_dimension = ContinuousDimension(name='continuous', min=0, max=10, include_min=include_min, include_max=include_max)
        serialized = OptimizerServiceEncoder.encode_continuous_dimension(continuous_dimension)
        deserialized_continuous_dimension = OptimizerServiceDecoder.decode_continuous_dimension(serialized)
        assert isinstance(serialized, OptimizerService_pb2.ContinuousDimension)
        assert deserialized_continuous_dimension == continuous_dimension

    def test_discrete_dimension(self):
        discrete_dimension = DiscreteDimension(name='discrete', min=1, max=100)
        serialized = OptimizerServiceEncoder.encode_discrete_dimension(discrete_dimension)
        deserialized = OptimizerServiceDecoder.decode_discrete_dimension(serialized)
        assert isinstance(serialized, OptimizerService_pb2.DiscreteDimension)
        assert discrete_dimension == deserialized

    def test_ordinal_dimension(self):
        ordinal_dimension = OrdinalDimension(name='ordinal', ordered_values=['good', 'better', 'best'])
        serialized = OptimizerServiceEncoder.encode_ordinal_dimension(ordinal_dimension)
        deserialized = OptimizerServiceDecoder.decode_ordinal_dimension(serialized)
        assert deserialized == ordinal_dimension
        assert isinstance(serialized, OptimizerService_pb2.OrdinalDimension)

    def test_composite_dimension(self):
        original_A = ContinuousDimension(name='x', min=0, max=1)
        original_B = ContinuousDimension(name='x', min=2, max=3)
        original_C = ContinuousDimension(name='x', min=2.5, max=3.5)
        original_D = original_A.union(original_B) - original_C
        original_E = original_B - original_C
        original_F = original_A.union(original_E)

        serialized_A = OptimizerServiceEncoder.encode_continuous_dimension(original_A)
        serialized_B = OptimizerServiceEncoder.encode_continuous_dimension(original_B)
        serialized_C = OptimizerServiceEncoder.encode_continuous_dimension(original_C)
        serialized_D = OptimizerServiceEncoder.encode_composite_dimension(original_D)
        serialized_E = OptimizerServiceEncoder.encode_continuous_dimension(original_E)
        serialized_F = OptimizerServiceEncoder.encode_composite_dimension(original_F)

        A = OptimizerServiceDecoder.decode_continuous_dimension(serialized_A)
        B = OptimizerServiceDecoder.decode_continuous_dimension(serialized_B)
        C = OptimizerServiceDecoder.decode_continuous_dimension(serialized_C)
        D = OptimizerServiceDecoder.decode_composite_dimension(serialized_D)
        E = OptimizerServiceDecoder.decode_continuous_dimension(serialized_E)
        F = OptimizerServiceDecoder.decode_composite_dimension(serialized_F)

        assert A in original_A
        assert B in original_B
        assert C in original_C
        assert D in original_D
        assert E in original_E
        assert F in original_F

        assert original_A in A
        assert original_B in B
        assert original_C in C
        assert original_D in D
        assert original_E in E
        assert original_F in F

        assert 0.5 in D
        assert 1.5 not in D
        assert 2.5 not in D
        assert 3.4 not in D
        assert 35 not in D
        assert 2 in E
        assert 2.5 not in E
        assert 0 in F and 1 in F and 1.5 not in F and 2 in F and 2.5 not in F


    def test_hypergrid(self):
        parameter_space = bayesian_optimizer_config_store.parameter_space
        serialized = OptimizerServiceEncoder.encode_simple_hypergrid(parameter_space)
        deserialized = OptimizerServiceDecoder.decode_simple_hypergrid(serialized)

        print(deserialized)

        for _ in range(1000):
            assert deserialized.random() in parameter_space
