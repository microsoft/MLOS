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
            },
            "children": [
                {
                    "name": "Mock Environment",
                    "class": "mlos_bench.environments.mock_env.MockEnv",
                    "config": {
                        "tunable_params": ["provision"],
                        "const_args": {
                            "vmName": "Placeholder VM",
                            "other_param": 99,
                        },
                        "required_args": ["vmName"],
                        "range": [60, 120],
                        "metrics": ["score", "other_score"],
                    }
                }
            ]
        },
        tunables=tunable_groups,
        service=ConfigPersistenceService({}),
    )


def test_composite_env(composite_env: CompositeEnv, tunable_groups: TunableGroups) -> None:
    """
    Check that the const_args from the parent environment get propagated to the children.
    """
    assert composite_env.setup(tunable_groups)
    assert composite_env.children[0].parameters == {
        "vmName": "Mock VM",                    # const_args from the parent
        "other_param": 99,                      # const_args from the child
        "vmSize": "Standard_B4ms",              # tunable_params from the parent
    }
