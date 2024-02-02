#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Common fixtures for mock TunableGroups.
"""

from typing import Any, Dict

import pytest

import json5 as json

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.tunables.covariant_group import CovariantTunableGroup
from mlos_bench.tunables.tunable_groups import TunableGroups

# pylint: disable=redefined-outer-name

TUNABLE_GROUPS_JSON = """
{
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
            "idle": {
                "description": "Idling method",
                "type": "categorical",
                "default": "halt",
                "values": ["halt", "mwait", "noidle"],
                "values_weights": [33, 33, 33]  // FLAML requires uniform weights
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
                "special": [-1, 0],
                // FLAML requires uniform weights, separately for
                // specials and switching between specials and range.
                "special_weights": [0.25, 0.25],
                "range_weight": 0.5
            },
            "kernel_sched_latency_ns": {
                "description": "Initial value for the scheduler period",
                "type": "int",
                "default": 2000000,
                "range": [0, 1000000000]
            }
        }
    }
}
"""


@pytest.fixture
def tunable_groups_config() -> Dict[str, Any]:
    """
    Fixture to get the JSON string for the tunable groups.
    """
    conf = json.loads(TUNABLE_GROUPS_JSON)
    assert isinstance(conf, dict)
    ConfigSchema.TUNABLE_PARAMS.validate(conf)
    return conf


@pytest.fixture
def tunable_groups(tunable_groups_config: dict) -> TunableGroups:
    """
    A test fixture that produces a mock TunableGroups.

    Returns
    -------
    tunable_groups : TunableGroups
        A new TunableGroups object for testing.
    """
    tunables = TunableGroups(tunable_groups_config)
    tunables.reset()
    return tunables


@pytest.fixture
def covariant_group(tunable_groups: TunableGroups) -> CovariantTunableGroup:
    """
    Text fixture to get a CovariantTunableGroup from tunable_groups.

    Returns
    -------
    CovariantTunableGroup
    """
    (_, covariant_group) = next(iter(tunable_groups))
    return covariant_group
