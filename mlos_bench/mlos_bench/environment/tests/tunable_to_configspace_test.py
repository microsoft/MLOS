"""
Unit tests for Tunable to ConfigSpace conversion.
"""

import pytest

from ConfigSpace import UniformIntegerHyperparameter
from ConfigSpace import UniformFloatHyperparameter
from ConfigSpace import CategoricalHyperparameter

from mlos_bench.environment import Tunable, TunableGroups
from mlos_bench.convert_configspace import _tunable_to_hyperparameter
from mlos_bench.convert_configspace import tunable_groups_to_configspace

# pylint: disable=redefined-outer-name,protected-access


@pytest.fixture
def tunable_categorical() -> Tunable:
    """
    A test fixture for a categorical Tunable object.

    Returns
    -------
    tunable : Tunable
        An instance of a categorical Tunable.
    """
    return Tunable("vmSize", {
        "description": "Azure VM size",
        "type": "categorical",
        "default": "Standard_B4ms",
        "values": ["Standard_B2s", "Standard_B2ms", "Standard_B4ms"]
    })


@pytest.fixture
def tunable_int() -> Tunable:
    """
    A test fixture for an integer Tunable object.

    Returns
    -------
    tunable : Tunable
        An instance of an integer Tunable.
    """
    return Tunable("kernel_sched_migration_cost_ns", {
        "description": "Cost of migrating the thread to another core",
        "type": "int",
        "default": -1,
        "range": [-1, 500000],
        "special": [-1]
    })


@pytest.fixture
def tunable_float() -> Tunable:
    """
    A test fixture for a float Tunable object.

    Returns
    -------
    tunable : Tunable
        An instance of a float Tunable.
    """
    return Tunable("chaos_monkey_prob", {
        "description": "Probability of spontaneous VM shutdown",
        "type": "float",
        "default": 0.01,
        "range": [0, 1]
    })


@pytest.fixture
def tunable_groups() -> TunableGroups:
    """
    A test fixture that produces a mock TunableGroups.
    Returns
    -------
    tunable_groups : TunableGroups
        A new TunableGroups object for testing.
    """
    tunables = TunableGroups({
        "provision": {
            "cost": 1000,
            "params": {
                "vmSize": {
                    "description": "Azure VM size",
                    "type": "categorical",
                    "default": "Standard_B4ms",
                    "values": ["Standard_B2s", "Standard_B2ms", "Standard_B4ms"]
                }
            }
        },
        "boot": {
            "cost": 300,
            "params": {
                "rootfs": {
                    "description": "Root file system",
                    "type": "categorical",
                    "default": "xfs",
                    "values": ["xfs", "ext4", "ext2"]
                }
            }
        },
        "kernel": {
            "cost": 1,
            "params": {
                "kernel_sched_migration_cost_ns": {
                    "description": "Cost of migrating the thread to another core",
                    "type": "int",
                    "default": -1,
                    "range": [-1, 500000],
                    "special": [-1]
                }
            }
        }
    })
    tunables.reset()
    return tunables


def _cmp_tunable_hyperparameter_categorical(
        tunable: Tunable, cs_param: CategoricalHyperparameter):
    """
    Check if categorical Tunable and ConfigSpace Hyperparameter actually match.
    """
    assert isinstance(cs_param, CategoricalHyperparameter)
    assert set(cs_param.choices) == set(tunable._values)
    assert cs_param.default_value == tunable.value


def _cmp_tunable_hyperparameter_int(
        tunable: Tunable, cs_param: UniformIntegerHyperparameter):
    """
    Check if integer Tunable and ConfigSpace Hyperparameter actually match.
    """
    assert isinstance(cs_param, UniformIntegerHyperparameter)
    assert (cs_param.lower, cs_param.upper) == tuple(tunable._range)
    assert cs_param.default_value == tunable.value


def _cmp_tunable_hyperparameter_float(
        tunable: Tunable, cs_param: UniformFloatHyperparameter):
    """
    Check if float Tunable and ConfigSpace Hyperparameter actually match.
    """
    assert isinstance(cs_param, UniformFloatHyperparameter)
    assert (cs_param.lower, cs_param.upper) == tuple(tunable._range)
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


def test_tunable_groups_to_configspace(tunable_groups: TunableGroups):
    """
    Check the conversion of the entire TunableGroups collection
    to a list of ConfigSpace Hyperparameter objects.
    """
    cs_hyperparams = {param.name: param
                      for param in tunable_groups_to_configspace(tunable_groups)}
    for group in tunable_groups._tunable_groups.values():
        for (name, tunable) in group._tunables.items():
            cs_param = cs_hyperparams[name]
            assert cs_param.default_value == tunable.value
            if tunable._type == "int":
                _cmp_tunable_hyperparameter_int(tunable, cs_param)
            elif tunable._type == "float":
                _cmp_tunable_hyperparameter_float(tunable, cs_param)
            elif tunable._type == "categorical":
                _cmp_tunable_hyperparameter_categorical(tunable, cs_param)
            else:
                assert False, "Invalid tunable type"
