#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for grid search mlos_bench optimizer.
"""

from typing import Dict, Iterable

import itertools
import math
import random

import pytest

from mlos_bench.environments.status import Status
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
def grid_search_tunables_grid(grid_search_tunables: TunableGroups) -> Iterable[Dict[str, TunableValue]]:
    """
    Test fixture for grid from tunable groups.
    Used to check that the grids are the same (ignoring order).
    """
    tunables_params_values = [tunable.values for tunable, _group in grid_search_tunables if tunable.values is not None]
    tunable_names = tuple(tunable.name for tunable, _group in grid_search_tunables)
    return (dict(zip(tunable_names, combo)) for combo in itertools.product(*tunables_params_values))


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
                          grid_search_tunables_grid: Iterable[Dict[str, TunableValue]]) -> None:
    """
    Make sure that grid search optimizer initializes and works correctly.
    """
    expected_grid_size = math.prod(tunable.cardinality for tunable, _group in grid_search_tunables)
    assert expected_grid_size > len(grid_search_tunables)
    assert len(list(grid_search_tunables_grid)) == expected_grid_size
    assert set(grid_search_opt.pending_configs) == set(grid_search_tunables_grid)


def test_grid_search(grid_search_opt: GridSearchOptimizer,
                     grid_search_tunables: TunableGroups,
                     grid_search_tunables_grid: Iterable[Dict[str, TunableValue]]) -> None:
    """
    Make sure that grid search optimizer initializes and works correctly.
    """
    grid_search_tunables_grid_set = set(grid_search_tunables_grid)
    score = 1.0
    status = Status.SUCCEEDED
    suggestion = grid_search_opt.suggest()
    default_config = grid_search_tunables.restore_defaults().get_param_values()

    # First suggestion should be the defaults.
    assert suggestion.get_param_values() == default_config
    # But that shouldn't be the first element in the grid search.
    assert suggestion.get_param_values() != next(iter(grid_search_tunables_grid))
    # The suggestion should no longer be in the pending_configs.
    assert suggestion.get_param_values() not in grid_search_opt.pending_configs
    # But it should be in the suggested_configs now.
    assert grid_search_opt.suggested_configs == {default_config}

    # Register a score for that suggestion.
    grid_search_opt.register(suggestion, status, score)
    # Now it shouldn't be in the suggested_configs.
    assert len(list(grid_search_opt.suggested_configs)) == 0

    grid_search_tunables_grid_set.remove(default_config)
    assert set(grid_search_opt.pending_configs) == grid_search_tunables_grid_set

    # The next suggestion should be a different element in the grid search.
    suggestion = grid_search_opt.suggest()
    assert suggestion.get_param_values() != default_config
    assert suggestion.get_param_values() not in grid_search_opt.pending_configs
    assert suggestion.get_param_values() in grid_search_opt.suggested_configs
    grid_search_opt.register(suggestion, status, score)
    assert suggestion.get_param_values() not in grid_search_opt.pending_configs
    assert suggestion.get_param_values() not in grid_search_opt.suggested_configs

    grid_search_tunables_grid_set.remove(suggestion.get_param_values())
    assert set(grid_search_opt.pending_configs) == grid_search_tunables_grid_set

    # Try to empty the rest of the grid.
    while grid_search_opt.pending_configs:
        suggestion = grid_search_opt.suggest()
        grid_search_opt.register(suggestion, status, score)

    # The grid search should be empty now.
    assert not grid_search_opt.pending_configs
    assert not grid_search_opt.suggested_configs


def test_grid_search_async_order(grid_search_opt: GridSearchOptimizer) -> None:
    """
    Make sure that grid search optimizer works correctly when suggest and register
    are called out of order.
    """
    score = 1.0
    status = Status.SUCCEEDED
    suggest_count = 10
    suggested = [grid_search_opt.suggest() for _ in range(suggest_count)]
    suggested_shuffled = suggested.copy()
    random.shuffle(suggested_shuffled)
    assert suggested != suggested_shuffled

    for suggestion in suggested_shuffled:
        assert suggestion.get_param_values() not in set(grid_search_opt.pending_configs)
        assert suggestion.get_param_values() in grid_search_opt.suggested_configs
        grid_search_opt.register(suggestion, status, score)
        assert suggestion.get_param_values() not in grid_search_opt.suggested_configs

    best_score, best_config = grid_search_opt.get_best_observation()
    assert best_score == score

    # test re-register with higher score
    best_suggestion = suggested_shuffled[0]
    assert best_suggestion.get_param_values() not in set(grid_search_opt.pending_configs)
    assert best_suggestion.get_param_values() not in grid_search_opt.suggested_configs
    best_suggestion_score = score - 1 if grid_search_opt.direction == "min" else score + 1
    grid_search_opt.register(best_suggestion, status, best_suggestion_score)
    assert best_suggestion.get_param_values() not in grid_search_opt.suggested_configs

    best_score, best_config = grid_search_opt.get_best_observation()
    assert best_score == best_suggestion_score
    assert best_config == best_suggestion

    # Check bulk register
    suggested = [grid_search_opt.suggest() for _ in range(suggest_count)]
    assert all(suggestion.get_param_values() not in grid_search_opt.pending_configs for suggestion in suggested)
    assert all(suggestion.get_param_values() in grid_search_opt.suggested_configs for suggestion in suggested)

    # Those new suggestions also shouldn't be in the set of previously suggested configs.
    assert all(suggestion.get_param_values() not in suggested_shuffled for suggestion in suggested)

    grid_search_opt.bulk_register([suggestion.get_param_values() for suggestion in suggested],
                                  [score] * len(suggested),
                                  [status] * len(suggested))

    assert all(suggestion.get_param_values() not in grid_search_opt.pending_configs for suggestion in suggested)
    assert all(suggestion.get_param_values() not in grid_search_opt.suggested_configs for suggestion in suggested)

    best_score, best_config = grid_search_opt.get_best_observation()
    assert best_score == best_suggestion_score
    assert best_config == best_suggestion
