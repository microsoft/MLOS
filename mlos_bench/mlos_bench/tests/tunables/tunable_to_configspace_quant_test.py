#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for ConfigSpace quantization monkey patching."""

import numpy as np
from ConfigSpace import UniformFloatHyperparameter, UniformIntegerHyperparameter

from mlos_bench.optimizers.convert_configspace import _monkey_patch_quantization
from mlos_bench.tests import SEED


def test_configspace_quant_int() -> None:
    """Check the quantization of an integer hyperparameter."""
    quantized_values = set(range(0, 101, 10))
    hp = UniformIntegerHyperparameter("hp", lower=0, upper=100, log=False)

    # Before patching: expect that at least one value is not quantized.
    assert not set(hp.sample_value(100)).issubset(quantized_values)

    _monkey_patch_quantization(hp, 11)
    # After patching: *all* values must belong to the set of quantized values.
    assert hp.sample_value() in quantized_values  # check scalar type
    assert set(hp.sample_value(100)).issubset(quantized_values)  # batch version


def test_configspace_quant_float() -> None:
    """Check the quantization of a float hyperparameter."""
    quantized_values = set(np.linspace(0, 1, num=5, endpoint=True))
    hp = UniformFloatHyperparameter("hp", lower=0, upper=1, log=False)

    # Before patching: expect that at least one value is not quantized.
    assert not set(hp.sample_value(100)).issubset(quantized_values)

    # 5 is a nice number of bins to avoid floating point errors.
    _monkey_patch_quantization(hp, 5)
    # After patching: *all* values must belong to the set of quantized values.
    assert hp.sample_value() in quantized_values  # check scalar type
    assert set(hp.sample_value(100)).issubset(quantized_values)  # batch version


def test_configspace_quant_repatch() -> None:
    """Repatch the same hyperparameter with different number of bins."""
    quantized_values = set(range(0, 101, 10))
    hp = UniformIntegerHyperparameter("hp", lower=0, upper=100, log=False)

    # Before patching: expect that at least one value is not quantized.
    assert not set(hp.sample_value(100)).issubset(quantized_values)

    _monkey_patch_quantization(hp, 11)
    # After patching: *all* values must belong to the set of quantized values.
    samples = hp.sample_value(100, seed=np.random.RandomState(SEED))
    assert set(samples).issubset(quantized_values)

    # Patch the same hyperparameter again and check that the results are the same.
    _monkey_patch_quantization(hp, 11)
    # After patching: *all* values must belong to the set of quantized values.
    assert all(samples == hp.sample_value(100, seed=np.random.RandomState(SEED)))

    # Repatch with the higher number of bins and make sure we get new values.
    _monkey_patch_quantization(hp, 21)
    samples_set = set(hp.sample_value(100))
    assert samples_set.issubset(set(range(0, 101, 5)))
    assert samples_set.issuperset(set(range(5, 96, 10)))
    assert samples_set.issuperset(set(range(0, 101, 10)))
