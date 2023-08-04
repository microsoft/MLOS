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
                "vm_server_name": "Mock Server VM",
                "vm_client_name": "Mock Client VM",
                "someConst": "root"
            },
            "children": [
                {
                    "name": "Mock Client Environment 1",
                    "class": "mlos_bench.environments.mock_env.MockEnv",
                    "config": {
                        "tunable_params": ["provision"],
                        "const_args": {
                            "vmName": "$vm_client_name",
                            "EnvId": 1,
                        },
                        "required_args": ["vmName", "someConst"],
                        "range": [60, 120],
                        "metrics": ["score"],
                    }
                },
                {
                    "name": "Mock Server Environment 2",
                    "class": "mlos_bench.environments.mock_env.MockEnv",
                    "config": {
                        "tunable_params": ["boot"],
                        "const_args": {
                            "vmName": "$vm_server_name",
                            "EnvId": 2,
                        },
                        "required_args": ["vmName"],
                        "range": [60, 120],
                        "metrics": ["score"],
                    }
                },
                {
                    "name": "Mock Control Environment 3",
                    "class": "mlos_bench.environments.mock_env.MockEnv",
                    "config": {
                        "tunable_params": ["boot"],
                        "const_args": {
                            "vmName": "Mock Control VM",
                            "EnvId": 3,
                        },
                        "required_args": ["vmName", "vm_server_name", "vm_client_name"],
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
    NOTE: The current logic is that variables flow down via required_args and const_args, parent
    """
    assert composite_env.children[0].parameters == {
        "vmName": "Mock Client VM",     # const_args from the parent thru variable substitution
        "EnvId": 1,                     # const_args from the child
        "vmSize": "Standard_B4ms",      # tunable_params from the parent
        "someConst": "root",            # pulled in from parent via required_args
    }
    assert composite_env.children[1].parameters == {
        "vmName": "Mock Server VM",     # const_args from the parent
        "EnvId": 2,                     # const_args from the child
        "idle": "halt",                 # tunable_params from the parent
        # "someConst": "root"           # not required, so not passed from the parent
    }
    assert composite_env.children[2].parameters == {
        "vmName": "Mock Control VM",     # const_args from the parent
        "EnvId": 3,                     # const_args from the child
        "idle": "halt",                 # tunable_params from the parent
        # "someConst": "root"           # not required, so not passed from the parent
        "vm_client_name": "Mock Client VM",
        "vm_server_name": "Mock Server VM"
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

    with composite_env as env_context:
        assert env_context.setup(tunable_groups)

    assert composite_env.children[0].parameters == {
        "vmName": "Mock Client VM",     # const_args from the parent
        "EnvId": 1,                     # const_args from the child
        "vmSize": "Standard_B2s",       # tunable_params from the parent
        "someConst": "root",            # pulled in from parent via required_args
    }
    assert composite_env.children[1].parameters == {
        "vmName": "Mock Server VM",     # const_args from the parent
        "EnvId": 2,                     # const_args from the child
        "idle": "mwait",                # tunable_params from the parent
        # "someConst": "root"           # not required, so not passed from the parent
    }
    assert composite_env.children[2].parameters == {
        "vmName": "Mock Control VM",    # const_args from the parent
        "EnvId": 3,                     # const_args from the child
        "idle": "mwait",                # tunable_params from the parent
        "vm_client_name": "Mock Client VM",
        "vm_server_name": "Mock Server VM",
    }


@pytest.fixture
def nested_composite_env(tunable_groups: TunableGroups) -> CompositeEnv:
    """
    Test fixture for CompositeEnv.
    """
    return CompositeEnv(
        name="Composite Test Environment",
        config={
            "tunable_params": ["provision", "boot"],
            "const_args": {
                "vm_server_name": "Mock Server VM",
                "vm_client_name": "Mock Client VM",
                "someConst": "root"
            },
            "children": [
                {
                    "name": "Nested Composite Client Environment 1",
                    "class": "mlos_bench.environments.composite_env.CompositeEnv",
                    "config": {
                        "tunable_params": ["provision"],
                        "const_args": {
                            "vmName": "$vm_client_name",
                            "EnvId": 1,
                        },
                        "required_args": ["vmName", "EnvId", "someConst", "vm_server_name"],
                        "children": [
                            {
                                "name": "Mock Client Environment 1",
                                "class": "mlos_bench.environments.mock_env.MockEnv",
                                "config": {
                                    "tunable_params": ["provision"],
                                    # TODO: Might be nice to include a "^" or "*" option
                                    # here to indicate that all required_args from
                                    # the parent should be included here too in
                                    # order to reduce duplication.
                                    "required_args": ["vmName", "EnvId", "someConst", "vm_server_name"],
                                    "range": [60, 120],
                                    "metrics": ["score"],
                                }
                            },
                            # ...
                        ],
                    },
                },
                {
                    "name": "Nested Composite Server Environment 2",
                    "class": "mlos_bench.environments.composite_env.CompositeEnv",
                    "config": {
                        "tunable_params": ["boot"],
                        "const_args": {
                            "vmName": "$vm_server_name",
                            "EnvId": 2,
                        },
                        "required_args": ["vmName", "EnvId", "vm_client_name"],
                        "children": [
                            {
                                "name": "Mock Server Environment 2",
                                "class": "mlos_bench.environments.mock_env.MockEnv",
                                "config": {
                                    "tunable_params": ["boot"],
                                    "required_args": ["vmName", "EnvId", "vm_client_name"],
                                    "range": [60, 120],
                                    "metrics": ["score"],
                                }
                            },
                            # ...
                        ],
                    },
                },

            ]
        },
        tunables=tunable_groups,
        service=ConfigPersistenceService({}),
    )


def test_nested_composite_env_params(nested_composite_env: CompositeEnv) -> None:
    """
    Check that the const_args from the parent environment get propagated to the children.
    NOTE: The current logic is that variables flow down via required_args and const_args, parent
    """
    assert isinstance(nested_composite_env.children[0], CompositeEnv)
    assert nested_composite_env.children[0].children[0].parameters == {
        "vmName": "Mock Client VM",     # const_args from the parent thru variable substitution
        "EnvId": 1,                     # const_args from the child
        "vmSize": "Standard_B4ms",      # tunable_params from the parent
        "someConst": "root",            # pulled in from parent via required_args
        "vm_server_name": "Mock Server VM",
    }
    assert isinstance(nested_composite_env.children[1], CompositeEnv)
    assert nested_composite_env.children[1].children[0].parameters == {
        "vmName": "Mock Server VM",     # const_args from the parent
        "EnvId": 2,                     # const_args from the child
        "idle": "halt",                 # tunable_params from the parent
        # "someConst": "root"           # not required, so not passed from the parent
        "vm_client_name": "Mock Client VM",
    }


def test_nested_composite_env_setup(nested_composite_env: CompositeEnv, tunable_groups: TunableGroups) -> None:
    """
    Check that the child environments update their tunable parameters.
    """
    tunable_groups.assign({
        "vmSize": "Standard_B2s",
        "idle": "mwait",
        "kernel_sched_migration_cost_ns": 100000,
    })

    with nested_composite_env as env_context:
        assert env_context.setup(tunable_groups)

    assert isinstance(nested_composite_env.children[0], CompositeEnv)
    assert nested_composite_env.children[0].children[0].parameters == {
        "vmName": "Mock Client VM",     # const_args from the parent
        "EnvId": 1,                     # const_args from the child
        "vmSize": "Standard_B2s",       # tunable_params from the parent
        "someConst": "root",            # pulled in from parent via required_args
        "vm_server_name": "Mock Server VM",
    }

    assert isinstance(nested_composite_env.children[1], CompositeEnv)
    assert nested_composite_env.children[1].children[0].parameters == {
        "vmName": "Mock Server VM",     # const_args from the parent
        "EnvId": 2,                     # const_args from the child
        "idle": "mwait",                # tunable_params from the parent
        # "someConst": "root"           # not required, so not passed from the parent
        "vm_client_name": "Mock Client VM",
    }
