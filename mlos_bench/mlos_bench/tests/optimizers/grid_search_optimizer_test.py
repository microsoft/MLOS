#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for grid search mlos_bench optimizer.
"""

import pytest

from mlos_bench.optimizers.grid_search_optimizer import GridSearchOptimizer
from mlos_bench.tunables.tunable_groups import TunableGroups


# pylint: disable=redefined-outer-name

@pytest.fixture
def grid_search_tunables_config() -> dict:
    """
    Test fixture for grid search optimizer tunables config.
    """
    return {
            "grid": {
                "cost": 1,
                "params": {
                    "cat": {
                        "type": "categorical",
                        "values": ["a", "b", "c"],
                        "default": "a",
                    },
                    "int": {
                        "type": "int",
                        "range": [1, 3],
                        "default": 2,
                    },
                    "float": {
                        "type": "float",
                        "range": [0, 1],
                        "default": 0.5,
                        "quantization": 0.25,
                    },
                },
            },
        }


@pytest.fixture
def grid_search_tunables(grid_search_tunables_config: dict) -> TunableGroups:
    """
    Test fixture for grid search optimizer tunables.
    """
    return TunableGroups(grid_search_tunables_config)


@pytest.fixture
def grid_search_opt(grid_search_tunables: TunableGroups) -> GridSearchOptimizer:
    """
    Test fixture for grid search optimizer.
    """
    return GridSearchOptimizer(tunables=grid_search_tunables, config={})


def test_grid_search_grid(grid_search_opt: GridSearchOptimizer) -> None:
    """
    Make sure that grid search optimizer initializes and works correctly.
    """
    # pylint: disable=protected-access
    print(grid_search_opt.configs)
    assert False
