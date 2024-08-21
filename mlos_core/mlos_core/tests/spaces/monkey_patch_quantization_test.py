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
    QUANTIZATION_BINS_META_KEY,
    monkey_patch_cs_quantization,
    monkey_patch_hp_quantization,
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

    # Before patching: expect that at least one value is not quantized.
    assert not set(hp.sample_value(100)).issubset(quantized_values)

    monkey_patch_hp_quantization(hp)
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

    # Before patching: expect that at least one value is not quantized.
    assert not set(hp.sample_value(100)).issubset(quantized_values)

    monkey_patch_hp_quantization(hp)
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

    # Before patching: expect that at least one value is not quantized.
    assert not set(hp.sample_value(100)).issubset(quantized_values)

    monkey_patch_hp_quantization(hp)
    # After patching: *all* values must belong to the set of quantized values.
    samples = hp.sample_value(100, seed=RandomState(SEED))
    assert set(samples).issubset(quantized_values)

    # Patch the same hyperparameter again and check that the results are the same.
    monkey_patch_hp_quantization(hp)
    # After patching: *all* values must belong to the set of quantized values.
    assert all(samples == hp.sample_value(100, seed=RandomState(SEED)))

    # Repatch with the higher number of bins and make sure we get new values.
    new_meta = dict(hp.meta or {})
    new_meta[QUANTIZATION_BINS_META_KEY] = 21
    hp.meta = new_meta
    monkey_patch_hp_quantization(hp)
    samples_set = set(hp.sample_value(100, seed=RandomState(SEED)))
    quantized_values_new = set(range(5, 96, 10))
    assert samples_set.issubset(set(range(0, 101, 5)))
    assert len(samples_set - quantized_values_new) < len(samples_set)

    # Repatch without quantization and make sure we get the original values.
    new_meta = dict(hp.meta or {})
    del new_meta[QUANTIZATION_BINS_META_KEY]
    hp.meta = new_meta
    assert hp.meta.get(QUANTIZATION_BINS_META_KEY) is None
    monkey_patch_hp_quantization(hp)
    samples_set = set(hp.sample_value(100, seed=RandomState(SEED)))
    assert samples_set.issubset(set(range(0, 101)))
    assert len(quantized_values_new) < len(quantized_values) < len(samples_set)


def test_configspace_quant() -> None:
    """Test quantization of multiple hyperparameters in the ConfigSpace."""
    space = ConfigurationSpace(
        name="cs_test",
        space={
            "hp_int": (0, 100000),
            "hp_int_quant": (0, 100000),
            "hp_float": (0.0, 1.0),
            "hp_categorical": ["a", "b", "c"],
            "hp_constant": 1337,
        },
    )
    space["hp_int_quant"].meta = {QUANTIZATION_BINS_META_KEY: 5}
    space["hp_float"].meta = {QUANTIZATION_BINS_META_KEY: 11}
    monkey_patch_cs_quantization(space)

    space.seed(SEED)
    assert dict(space.sample_configuration()) == {
        "hp_categorical": "c",
        "hp_constant": 1337,
        "hp_float": 0.6,
        "hp_int": 60263,
        "hp_int_quant": 0,
    }
    assert [dict(conf) for conf in space.sample_configuration(3)] == [
        {
            "hp_categorical": "a",
            "hp_constant": 1337,
            "hp_float": 0.4,
            "hp_int": 59150,
            "hp_int_quant": 50000,
        },
        {
            "hp_categorical": "a",
            "hp_constant": 1337,
            "hp_float": 0.3,
            "hp_int": 65725,
            "hp_int_quant": 75000,
        },
        {
            "hp_categorical": "b",
            "hp_constant": 1337,
            "hp_float": 0.6,
            "hp_int": 84654,
            "hp_int_quant": 25000,
        },
    ]
