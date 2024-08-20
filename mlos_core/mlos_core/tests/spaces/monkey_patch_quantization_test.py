#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for ConfigSpace quantization monkey patching."""

import numpy as np
from ConfigSpace import (
    ConfigurationSpace,
    UniformFloatHyperparameter,
    UniformIntegerHyperparameter,
)
from numpy.random import RandomState

from mlos_core.spaces.converters.util import (
    monkey_patch_cs_quantization,
    QUANTIZATION_BINS_META_KEY,
)
from mlos_core.tests import SEED


def test_configspace_quant_int() -> None:
    """Check the quantization of an integer hyperparameter."""
    quantization_bins = 11
    quantized_values = set(range(0, 101, 10))
    hp = UniformIntegerHyperparameter(
        "hp",
        lower=0,
        upper=100,
        log=False,
        meta={QUANTIZATION_BINS_META_KEY: quantization_bins},
    )
    cs = ConfigurationSpace()
    cs.add(hp)

    # Before patching: expect that at least one value is not quantized.
    assert not set(hp.sample_value(100)).issubset(quantized_values)

    monkey_patch_cs_quantization(cs)
    # After patching: *all* values must belong to the set of quantized values.
    assert hp.sample_value() in quantized_values  # check scalar type
    assert set(hp.sample_value(100)).issubset(quantized_values)  # batch version


def test_configspace_quant_float() -> None:
    """Check the quantization of a float hyperparameter."""
    # 5 is a nice number of bins to avoid floating point errors.
    quantization_bins = 5
    quantized_values = set(np.linspace(0, 1, num=quantization_bins, endpoint=True))
    hp = UniformFloatHyperparameter(
        "hp",
        lower=0,
        upper=1,
        log=False,
        meta={QUANTIZATION_BINS_META_KEY: quantization_bins},
    )
    cs = ConfigurationSpace()
    cs.add(hp)

    # Before patching: expect that at least one value is not quantized.
    assert not set(hp.sample_value(100)).issubset(quantized_values)

    monkey_patch_cs_quantization(cs)
    # After patching: *all* values must belong to the set of quantized values.
    assert hp.sample_value() in quantized_values  # check scalar type
    assert set(hp.sample_value(100)).issubset(quantized_values)  # batch version


def test_configspace_quant_repatch() -> None:
    """Repatch the same hyperparameter with different number of bins."""
    quantization_bins = 11
    quantized_values = set(range(0, 101, 10))
    hp = UniformIntegerHyperparameter(
        "hp",
        lower=0,
        upper=100,
        log=False,
        meta={QUANTIZATION_BINS_META_KEY: quantization_bins},
    )
    cs = ConfigurationSpace()
    cs.add(hp)

    # Before patching: expect that at least one value is not quantized.
    assert not set(hp.sample_value(100)).issubset(quantized_values)

    monkey_patch_cs_quantization(cs)
    # After patching: *all* values must belong to the set of quantized values.
    samples = hp.sample_value(100, seed=RandomState(SEED))
    assert set(samples).issubset(quantized_values)

    # Patch the same hyperparameter again and check that the results are the same.
    monkey_patch_cs_quantization(cs)
    # After patching: *all* values must belong to the set of quantized values.
    assert all(samples == hp.sample_value(100, seed=RandomState(SEED)))

    # Repatch with the higher number of bins and make sure we get new values.
    new_meta = dict(hp.meta or {})
    new_meta[QUANTIZATION_BINS_META_KEY] = 21
    hp.meta = new_meta
    monkey_patch_cs_quantization(cs)
    samples_set = set(hp.sample_value(100, seed=RandomState(SEED)))
    quantized_values_new = set(range(5, 96, 10))
    assert samples_set.issubset(set(range(0, 101, 5)))
    assert len(samples_set - quantized_values_new) < len(samples_set)
