#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for Tunable to ConfigSpace conversion.
"""

import pytest

from ConfigSpace import (
    ConfigurationSpace,
    CategoricalHyperparameter,
    UniformIntegerHyperparameter,
    UniformFloatHyperparameter,
    EqualsCondition,
)

from mlos_bench.tunables.tunable import Tunable
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.optimizers.convert_configspace import (
    _tunable_to_configspace,
    tunable_groups_to_configspace,
    special_param_names,
)

# pylint: disable=redefined-outer-name


@pytest.fixture
def configuration_space() -> ConfigurationSpace:
    """
    A test fixture that produces a mock ConfigurationSpace object
    matching the tunable_groups fixture.

    Returns
    -------
    configuration_space : ConfigurationSpace
        A new ConfigurationSpace object for testing.
    """
    (ksm_special, ksm_type) = special_param_names("kernel_sched_migration_cost_ns")

    spaces = ConfigurationSpace(space={
        "vmSize": ["Standard_B2s", "Standard_B2ms", "Standard_B4ms"],
        "idle": ["halt", "mwait", "noidle"],
        "kernel_sched_migration_cost_ns": (0, 500000),
        ksm_special: [-1, 0],
        ksm_type: ["special", "range"],
        "kernel_sched_latency_ns": (0, 1000000000),
    })

    spaces["vmSize"].default_value = "Standard_B4ms"
    spaces["idle"].default_value = "halt"
    spaces["kernel_sched_migration_cost_ns"].default_value = 250000
    spaces[ksm_special].default_value = -1
    spaces[ksm_type].default_value = "special"
    spaces[ksm_type].probabilities = (0.5, 0.5)  # FLAML requires distribution to be uniform
    spaces["kernel_sched_latency_ns"].default_value = 2000000

    spaces.add_condition(EqualsCondition(
        spaces[ksm_special], spaces[ksm_type], "special"))
    spaces.add_condition(EqualsCondition(
        spaces["kernel_sched_migration_cost_ns"], spaces[ksm_type], "range"))

    return spaces


def _cmp_tunable_hyperparameter_categorical(
        tunable: Tunable, space: ConfigurationSpace) -> None:
    """
    Check if categorical Tunable and ConfigSpace Hyperparameter actually match.
    """
    param = space[tunable.name]
    assert isinstance(param, CategoricalHyperparameter)
    assert set(param.choices) == set(tunable.categories)
    assert param.default_value == tunable.value


def _cmp_tunable_hyperparameter_numerical(
        tunable: Tunable, space: ConfigurationSpace) -> None:
    """
    Check if integer Tunable and ConfigSpace Hyperparameter actually match.
    """
    param = space[tunable.name]
    assert isinstance(param, (UniformIntegerHyperparameter, UniformFloatHyperparameter))
    assert (param.lower, param.upper) == tuple(tunable.range)
    if tunable.in_range(tunable.value):
        assert param.default_value == tunable.value


def test_tunable_to_configspace_categorical(tunable_categorical: Tunable) -> None:
    """
    Check the conversion of Tunable to CategoricalHyperparameter.
    """
    cs_param = _tunable_to_configspace(tunable_categorical)
    _cmp_tunable_hyperparameter_categorical(tunable_categorical, cs_param)


def test_tunable_to_configspace_int(tunable_int: Tunable) -> None:
    """
    Check the conversion of Tunable to UniformIntegerHyperparameter.
    """
    cs_param = _tunable_to_configspace(tunable_int)
    _cmp_tunable_hyperparameter_numerical(tunable_int, cs_param)


def test_tunable_to_configspace_float(tunable_float: Tunable) -> None:
    """
    Check the conversion of Tunable to UniformFloatHyperparameter.
    """
    cs_param = _tunable_to_configspace(tunable_float)
    _cmp_tunable_hyperparameter_numerical(tunable_float, cs_param)


_CMP_FUNC = {
    "int": _cmp_tunable_hyperparameter_numerical,
    "float": _cmp_tunable_hyperparameter_numerical,
    "categorical": _cmp_tunable_hyperparameter_categorical,
}


def test_tunable_groups_to_hyperparameters(tunable_groups: TunableGroups) -> None:
    """
    Check the conversion of TunableGroups to ConfigurationSpace.
    Make sure that the corresponding Tunable and Hyperparameter objects match.
    """
    space = tunable_groups_to_configspace(tunable_groups)
    for (tunable, _group) in tunable_groups:
        _CMP_FUNC[tunable.type](tunable, space)


def test_tunable_groups_to_configspace(
        tunable_groups: TunableGroups, configuration_space: ConfigurationSpace) -> None:
    """
    Check the conversion of the entire TunableGroups collection
    to a single ConfigurationSpace object.
    """
    space = tunable_groups_to_configspace(tunable_groups)
    assert space == configuration_space
