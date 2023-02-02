"""
Common fixtures for Tunable and TunableGroups tests.
"""

import pytest

from mlos_bench.environment import Tunable, TunableGroups


@pytest.fixture
def tunable_categorical() -> Tunable:
    """
    A test fixture that produces a categorical Tunable object.

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
    A test fixture that produces an interger Tunable object with limited range.

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
    A test fixture that produces a float Tunable object with limited range.

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
