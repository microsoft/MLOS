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
            "const_args": {
                "vmName": "Mock VM",
                "someConst": "root"
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
                },
                {
                    "name": "Composite Child 3",
                    "class": "mlos_bench.environments.composite_env.CompositeEnv",
                    "config": {
                        "const_args": {
                            "vmName": "Nested Mock VM",
                            "EnvId": 3
                        },
                        "required_args": ["vmName"],
                        "children": [
                            {
                                "name": "Nested Mock Environment 1",
                                "class": "mlos_bench.environments.mock_env.MockEnv",
                                "config": {
                                    "tunable_params": ["provision"],
                                    "const_args": {
                                        "vmName": "Placeholder VM",
                                    },
                                    "required_args": ["vmName", "someConst"],
                                    "range": [60, 120],
                                    "metrics": ["score"],
                                }
                            },
                            {
                                "name": "Nested Mock Environment 2",
                                "class": "mlos_bench.environments.mock_env.MockEnv",
                                "config": {
                                    "tunable_params": ["boot"],
                                    "const_args": {
                                        "vmName": "Placeholder VM",
                                        "someConst": "leaf"
                                    },
                                    "required_args": ["vmName", "someConst"],
                                    "range": [60, 120],
                                    "metrics": ["score"],
                                }
                            }
                        ]
                    },
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
        #"someConst": "root"        # not required, so not passed from the parent
    }
    assert composite_env.children[1].parameters == {
        "vmName": "Mock VM",        # const_args from the parent
        "EnvId": 2,                 # const_args from the child
        "idle": "halt",             # tunable_params from the parent
        #"someConst": "root"        # not required, so not passed from the parent
    }
    assert isinstance(composite_env.children[2], CompositeEnv)
    # CompositeEnv child should receive everything from the parent since it didn't specify a tunable_params subgroup to filter on.
    # It should also override the const_args.
    new_params = composite_env.parameters.copy()
    new_params["vmName"] = "Nested Mock VM"
    new_params["EnvId"] = 3
    assert composite_env.children[2].parameters == new_params
    # Now check it's parents
    assert composite_env.children[2].children[0].parameters == {
        "vmName": "Nested Mock VM",     # const_args from the parent
        "EnvId": 3,                     # const_args from the parent
        "vmSize": "Standard_B4ms",      # tunable_params from the parent
        "someConst": "root"             # tunable_params from grandparent
    }
    assert composite_env.children[2].children[1].parameters == {
        "vmName": "Nested Mock VM",     # const_args from the parent
        "EnvId": 3,                     # const_args from the parent
        "idle": "halt",                 # tunable_params from the parent
        "someConst": "leaf"             # tunable_params from child
    }
    # Make sure it didn't alter the grand parent.
    assert composite_env.parameters == {
        "vmName": "Mock VM",            # const_args from the parent
        "someConst": "root"             # tunable_params from parent
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
