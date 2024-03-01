#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for grid search mlos_bench optimizer.
"""

from typing import Dict, Set, List

import itertools
import math

import pytest

from mlos_bench.environments.status import Status
from mlos_bench.tunables.hashable_tunable_values_dict import HashableTunableValuesDict
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
def grid_search_tunables_grid_set(grid_search_tunables: TunableGroups) -> Set[HashableTunableValuesDict]:
    """
    Test fixture for grid from tunable groups.
    Used to check that the grids are the same (ignoring order).
    """
    tunables_params_values = [tunable.values for tunable, _group in grid_search_tunables if tunable.values is not None]
    tunable_names = tuple(tunable.name for tunable, _group in grid_search_tunables)
    return {HashableTunableValuesDict(zip(tunable_names, combo)) for combo in itertools.product(*tunables_params_values)}


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
                          grid_search_tunables_grid_set: Set[HashableTunableValuesDict]) -> None:
    """
    Make sure that grid search optimizer initializes and works correctly.
    """
    expected_grid_size = math.prod(tunable.cardinality for tunable, _group in grid_search_tunables)
    assert expected_grid_size > len(grid_search_tunables)
    assert len(grid_search_tunables_grid_set) == expected_grid_size
    assert set(grid_search_opt.pending_configs) == grid_search_tunables_grid_set


def test_grid_search(grid_search_opt: GridSearchOptimizer,
                     grid_search_tunables: TunableGroups,
                     grid_search_tunables_grid_set: Set[HashableTunableValuesDict]) -> None:
    """
    Make sure that grid search optimizer initializes and works correctly.
    """
    score = 1.0
    status = Status.SUCCEEDED
    suggestion = grid_search_opt.suggest()
    default_config = grid_search_tunables.restore_defaults().get_param_values()

    # First suggestion should be the defaults.
    assert suggestion.get_param_values() == default_config
    # But that shouldn't be the first element in the grid search.
    assert suggestion.get_param_values() != next(iter(grid_search_tunables_grid_set))
    # The suggestion should no longer be in the pending_configs.
    assert suggestion.get_param_values() not in grid_search_opt.pending_configs
    # But it should be in the suggested_configs now.
    assert grid_search_opt.suggested_configs == {default_config}

    # Register a score for that suggestion.
    grid_search_opt.register(suggestion, status, score)
    # Now it shouldn't be in the suggested_configs.
    assert len(grid_search_opt.suggested_configs) == 0

    grid_search_tunables_grid_set.remove(default_config)
    assert set(grid_search_opt.pending_configs) == grid_search_tunables_grid_set

    # The next suggestion should be a different element in the grid search.
    suggestion = grid_search_opt.suggest()
    assert suggestion.get_param_values() != default_config
    grid_search_opt.register(suggestion, status, score)
    assert suggestion.get_param_values() not in grid_search_opt.pending_configs
    assert suggestion.get_param_values() in grid_search_opt.suggested_configs

    grid_search_tunables_grid_set.remove(suggestion.get_param_values())
    assert set(grid_search_opt.pending_configs) == grid_search_tunables_grid_set

    # Try to empty the rest of the grid.
    while grid_search_opt.pending_configs:
        suggestion = grid_search_opt.suggest()
        grid_search_opt.register(suggestion, status, score)

    # The grid search should be empty now.
    assert not grid_search_opt.pending_configs
    assert not grid_search_opt.suggested_configs


# TODO: Test multiple suggest and registers out of order.
# TODO: Test not starting with the defaults.
