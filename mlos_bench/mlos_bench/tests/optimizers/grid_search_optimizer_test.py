#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for grid search mlos_bench optimizer.
"""

from typing import Dict, Set

import itertools
import math

import pytest

from mlos_bench.hashable_dict import HashableDict
from mlos_bench.optimizers.grid_search_optimizer import GridSearchOptimizer
from mlos_bench.tunables.tunable import TunableValue
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
def grid_search_tunables_grid(grid_search_tunables: TunableGroups) -> Set[Dict[str, TunableValue]]:
    """
    Test fixture for grid from tunable groups
    """
    tunables_params_values = [tunable.values for tunable, _group in grid_search_tunables if tunable.values is not None]
    tunable_names = tuple(tunable.name for tunable, _group in grid_search_tunables)
    return set(HashableDict(zip(tunable_names, combo)) for combo in itertools.product(*tunables_params_values))


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
    assert len(grid_search_tunables) == 3
    return GridSearchOptimizer(tunables=grid_search_tunables, config={})


def test_grid_search_grid(grid_search_opt: GridSearchOptimizer,
                          grid_search_tunables: TunableGroups,
                          grid_search_tunables_grid: Set[Dict[str, TunableValue]]) -> None:
    """
    Make sure that grid search optimizer initializes and works correctly.
    """
    expected_grid_size = math.prod(tunable.cardinality for tunable, _group in grid_search_tunables)
    assert expected_grid_size > len(grid_search_tunables)
    assert len(grid_search_tunables_grid) == expected_grid_size
    assert grid_search_opt.configs == grid_search_tunables_grid
