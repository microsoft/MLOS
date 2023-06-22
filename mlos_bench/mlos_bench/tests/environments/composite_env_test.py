#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for composite environment.
"""

import pytest

from mlos_bench.environments.composite_env import CompositeEnv
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.services.config_persistence import ConfigPersistenceService

# pylint: disable=redefined-outer-name


@pytest.fixture
def composite_env(tunable_groups: TunableGroups) -> CompositeEnv:
    """
    Test fixture for CompositeEnv.
    """
    return CompositeEnv(
        name="Composite Test Environment",
        config={
            "tunable_params": ["provision", "boot"],
            "const_args": {
                "vmName": "Mock VM",
            },
            "children": [
                {
                    "name": "Mock Environment 1",
                    "class": "mlos_bench.environments.mock_env.MockEnv",
                    "config": {
                        "tunable_params": ["provision"],
                        "const_args": {
                            "vmName": "Placeholder VM",
                            "EnvId": 1,
                        },
                        "required_args": ["vmName"],
                        "range": [60, 120],
                        "metrics": ["score"],
                    }
                },
                {
                    "name": "Mock Environment 2",
                    "class": "mlos_bench.environments.mock_env.MockEnv",
                    "config": {
                        "tunable_params": ["boot"],
                        "const_args": {
                            "vmName": "Placeholder VM",
                            "EnvId": 2,
                        },
                        "required_args": ["vmName"],
                        "range": [60, 120],
                        "metrics": ["score"],
                    }
                }
            ]
        },
        tunables=tunable_groups,
        service=ConfigPersistenceService({}),
    )


def test_composite_env_params(composite_env: CompositeEnv) -> None:
    """
    Check that the const_args from the parent environment get propagated to the children.
    """
    assert composite_env.children[0].parameters == {
        "vmName": "Mock VM",        # const_args from the parent
        "EnvId": 1,                 # const_args from the child
        "vmSize": "Standard_B4ms",  # tunable_params from the parent
    }
    assert composite_env.children[1].parameters == {
        "vmName": "Mock VM",        # const_args from the parent
        "EnvId": 2,                 # const_args from the child
        "idle": "halt",             # tunable_params from the parent
    }


def test_composite_env_setup(composite_env: CompositeEnv, tunable_groups: TunableGroups) -> None:
    """
    Check that the child environments update their tunable parameters.
    """
    tunable_groups.assign({
        "vmSize": "Standard_B2s",
        "idle": "mwait",
        "kernel_sched_migration_cost_ns": 100000,
    })
    assert composite_env.setup(tunable_groups)
    assert composite_env.children[0].parameters == {
        "vmName": "Mock VM",        # const_args from the parent
        "EnvId": 1,                 # const_args from the child
        "vmSize": "Standard_B2s",   # tunable_params from the parent
    }
    assert composite_env.children[1].parameters == {
        "vmName": "Mock VM",        # const_args from the parent
        "EnvId": 2,                 # const_args from the child
        "idle": "mwait",            # tunable_params from the parent
    }
