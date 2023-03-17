#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for Tunable to ConfigSpace conversion.
"""

import pytest

from ConfigSpace import UniformIntegerHyperparameter
from ConfigSpace import UniformFloatHyperparameter
from ConfigSpace import CategoricalHyperparameter
from ConfigSpace import ConfigurationSpace

from mlos_bench.tunables import Tunable, TunableGroups

from mlos_bench.optimizer.convert_configspace import _tunable_to_hyperparameter
from mlos_bench.optimizer.convert_configspace import tunable_groups_to_configspace

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
    spaces = ConfigurationSpace(space={
        "vmSize": ["Standard_B2s", "Standard_B2ms", "Standard_B4ms"],
        "rootfs": ["xfs", "ext4", "ext2"],
        "kernel_sched_migration_cost_ns": (-1, 500000)
    })

    spaces["vmSize"].default_value = "Standard_B4ms"
    spaces["rootfs"].default_value = "xfs"
    spaces["kernel_sched_migration_cost_ns"].default_value = -1

    return spaces


def _cmp_tunable_hyperparameter_categorical(
        tunable: Tunable, cs_param: CategoricalHyperparameter):
    """
    Check if categorical Tunable and ConfigSpace Hyperparameter actually match.
    """
    assert isinstance(cs_param, CategoricalHyperparameter)
    assert set(cs_param.choices) == set(tunable.categorical_values)
    assert cs_param.default_value == tunable.value


def _cmp_tunable_hyperparameter_int(
        tunable: Tunable, cs_param: UniformIntegerHyperparameter):
    """
    Check if integer Tunable and ConfigSpace Hyperparameter actually match.
    """
    assert isinstance(cs_param, UniformIntegerHyperparameter)
    assert (cs_param.lower, cs_param.upper) == tuple(tunable.range)
    assert cs_param.default_value == tunable.value


def _cmp_tunable_hyperparameter_float(
        tunable: Tunable, cs_param: UniformFloatHyperparameter):
    """
    Check if float Tunable and ConfigSpace Hyperparameter actually match.
    """
    assert isinstance(cs_param, UniformFloatHyperparameter)
    assert (cs_param.lower, cs_param.upper) == tuple(tunable.range)
    assert cs_param.default_value == tunable.value


def test_tunable_to_hyperparameter_categorical(tunable_categorical):
    """
    Check the conversion of Tunable to CategoricalHyperparameter.
    """
    cs_param = _tunable_to_hyperparameter(tunable_categorical)
    _cmp_tunable_hyperparameter_categorical(tunable_categorical, cs_param)


def test_tunable_to_hyperparameter_int(tunable_int):
    """
    Check the conversion of Tunable to UniformIntegerHyperparameter.
    """
    cs_param = _tunable_to_hyperparameter(tunable_int)
    _cmp_tunable_hyperparameter_int(tunable_int, cs_param)


def test_tunable_to_hyperparameter_float(tunable_float):
    """
    Check the conversion of Tunable to UniformFloatHyperparameter.
    """
    cs_param = _tunable_to_hyperparameter(tunable_float)
    _cmp_tunable_hyperparameter_float(tunable_float, cs_param)


_CMP_FUNC = {
    "int": _cmp_tunable_hyperparameter_int,
    "float": _cmp_tunable_hyperparameter_float,
    "categorical": _cmp_tunable_hyperparameter_categorical
}


def test_tunable_groups_to_hyperparameters(tunable_groups: TunableGroups):
    """
    Check the conversion of TunableGroups to ConfigurationSpace.
    Make sure that the corresponding Tunable and Hyperparameter objects match.
    """
    space = tunable_groups_to_configspace(tunable_groups)
    for (tunable, _group) in tunable_groups:
        cs_param = space[tunable.name]
        assert cs_param.default_value == tunable.value
        _CMP_FUNC[tunable.type](tunable, cs_param)


def test_tunable_groups_to_configspace(
        tunable_groups: TunableGroups, configuration_space: ConfigurationSpace):
    """
    Check the conversion of the entire TunableGroups collection
    to a single ConfigurationSpace object.
    """
    space = tunable_groups_to_configspace(tunable_groups)
    assert space == configuration_space
