#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for mock benchmark environment.
"""

import pytest

from mlos_bench.environments.composite_env import CompositeEnv
from mlos_bench.tunables.tunable_groups import TunableGroups

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
                        "tunable_groups": ["provision"],
                        "required_args": ["vmName"],
                        "range": [60, 120],
                        "metrics": ["score", "other_score"],
                    }
                }
            ]
        },
        tunables=tunable_groups
    )


def test_composite_env(composite_env: CompositeEnv, tunable_groups: TunableGroups) -> None:
    """
    Check the default values of the mock environment.
    """
    assert composite_env.setup(tunable_groups)
    assert composite_env.parameters == {
        "vmName": "Mock VM",
        "vmSize": "Standard_B4ms",
    }
