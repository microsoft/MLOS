#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Common fixtures for mock TunableGroups and Environment objects.
"""

from typing import Any, Dict, List

import os

import json5 as json
import pytest

from mlos_bench.tests import SEED

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.tunables.covariant_group import CovariantTunableGroup
from mlos_bench.tunables.tunable_groups import TunableGroups

# pylint: disable=redefined-outer-name
# -- Ignore pylint complaints about pytest references to
# `tunable_groups` fixture as both a function and a parameter.


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
                "values": ["halt", "mwait", "noidle"]
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


@pytest.fixture
def mock_env(tunable_groups: TunableGroups) -> MockEnv:
    """
    Test fixture for MockEnv.
    """
    return MockEnv(
        name="Test Env",
        config={
            "tunable_params": ["provision", "boot", "kernel"],
            "seed": SEED,
            "range": [60, 120],
            "metrics": ["score"],
        },
        tunables=tunable_groups
    )


@pytest.fixture
def mock_env_no_noise(tunable_groups: TunableGroups) -> MockEnv:
    """
    Test fixture for MockEnv.
    """
    return MockEnv(
        name="Test Env No Noise",
        config={
            "tunable_params": ["provision", "boot", "kernel"],
            "range": [60, 120],
            "metrics": ["score", "other_score"],
        },
        tunables=tunable_groups
    )


# Fixtures to configure the pytest-docker plugin.


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig: pytest.Config) -> List[str]:
    """
    Returns the path to the docker-compose file.

    Parameters
    ----------
    pytestconfig : pytest.Config

    Returns
    -------
    str
        Path to the docker-compose file.
    """
    _ = pytestconfig  # unused
    return [
        os.path.join(os.path.dirname(__file__), "services", "remote", "ssh", "docker-compose.yml"),
        # Add additional configs as necessary here.
    ]


@pytest.fixture(scope="session")
def docker_compose_project_name() -> str:
    """
    Returns the name of the docker-compose project.

    Returns
    -------
    str
        Name of the docker-compose project.
    """
    return f"mlos_bench-test-{os.getpid()}"