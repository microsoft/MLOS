"""
Unit tests for deep copy of tunable objects and groups.
"""

import pytest

from mlos_bench.environment import Tunable, TunableGroups

# pylint: disable=redefined-outer-name


@pytest.fixture
def tunable_categorical() -> Tunable:
    """
    A test fixture that produces a categorical Tunable object.

    Returns
    -------
    tunable : Tunable
        A categorical Tunable object.
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
    A test fixture that produces an interger Tunable object with limited range.

    Returns
    -------
    tunable : Tunable
        An integer Tunable object.
    """
    return Tunable("kernel_sched_migration_cost_ns", {
        "description": "Cost of migrating the thread to another core",
        "type": "int",
        "default": -1,
        "range": [0, 500000],
        "special": [-1]
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
                    "range": [0, 500000],
                    "special": [-1]
                }
            }
        }
    })
    tunables.reset()
    return tunables


def test_copy_tunable_int(tunable_int):
    """
    Check if deep copy works for Tunable object.
    """
    tunable_copy = tunable_int.copy()
    assert tunable_int == tunable_copy
    tunable_copy.value += 200
    assert tunable_int != tunable_copy


def test_copy_tunable_groups(tunable_groups):
    """
    Check if deep copy works for TunableGroups object.
    """
    tunable_groups_copy = tunable_groups.copy()
    assert tunable_groups == tunable_groups_copy
    tunable_groups_copy["vmSize"] += "_different_value"
    assert tunable_groups_copy.is_updated()
    assert not tunable_groups.is_updated()
    assert tunable_groups != tunable_groups_copy
