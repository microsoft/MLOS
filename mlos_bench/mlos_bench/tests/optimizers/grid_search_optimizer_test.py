#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for grid search mlos_bench optimizer."""

import itertools
import math
import random
from typing import Dict, List

import pytest

from mlos_bench.environments.status import Status
from mlos_bench.optimizers.grid_search_optimizer import GridSearchOptimizer
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups

# pylint: disable=redefined-outer-name


@pytest.fixture
def grid_search_tunables_config() -> dict:
    """Test fixture for grid search optimizer tunables config."""
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
def grid_search_tunables_grid(
    grid_search_tunables: TunableGroups,
) -> List[Dict[str, TunableValue]]:
    """
    Test fixture for grid from tunable groups.

    Used to check that the grids are the same (ignoring order).
    """
    tunables_params_values = [
        tunable.values for tunable, _group in grid_search_tunables if tunable.values is not None
    ]
    tunable_names = tuple(
        tunable.name for tunable, _group in grid_search_tunables if tunable.values is not None
    )
    return list(
        dict(zip(tunable_names, combo)) for combo in itertools.product(*tunables_params_values)
    )


@pytest.fixture
def grid_search_tunables(grid_search_tunables_config: dict) -> TunableGroups:
    """Test fixture for grid search optimizer tunables."""
    return TunableGroups(grid_search_tunables_config)


@pytest.fixture
def grid_search_opt(
    grid_search_tunables: TunableGroups,
    grid_search_tunables_grid: List[Dict[str, TunableValue]],
) -> GridSearchOptimizer:
    """Test fixture for grid search optimizer."""
    assert len(grid_search_tunables) == 3
    # Test the convergence logic by controlling the number of iterations to be not a
    # multiple of the number of elements in the grid.
    max_iterations = len(grid_search_tunables_grid) * 2 - 3
    return GridSearchOptimizer(
        tunables=grid_search_tunables,
        config={
            "max_suggestions": max_iterations,
            "optimization_targets": {"score": "max", "other_score": "min"},
        },
    )


def test_grid_search_grid(
    grid_search_opt: GridSearchOptimizer,
    grid_search_tunables: TunableGroups,
    grid_search_tunables_grid: List[Dict[str, TunableValue]],
) -> None:
    """Make sure that grid search optimizer initializes and works correctly."""
    # Check the size.
    expected_grid_size = math.prod(tunable.cardinality for tunable, _group in grid_search_tunables)
    assert expected_grid_size > len(grid_search_tunables)
    assert len(grid_search_tunables_grid) == expected_grid_size
    # Check for specific example configs inclusion.
    expected_config_example: Dict[str, TunableValue] = {
        "cat": "a",
        "int": 2,
        "float": 0.75,
    }
    grid_search_opt_pending_configs = list(grid_search_opt.pending_configs)
    assert expected_config_example in grid_search_tunables_grid
    assert expected_config_example in grid_search_opt_pending_configs
    # Check the rest of the contents.
    # Note: ConfigSpace param name vs TunableGroup parameter name order is not
    # consistent, so we need to full dict comparison.
    assert len(grid_search_opt_pending_configs) == expected_grid_size
    assert all(config in grid_search_tunables_grid for config in grid_search_opt_pending_configs)
    assert all(config in grid_search_opt_pending_configs for config in grid_search_tunables_grid)
    # Order is less relevant to us, so we'll just check that the sets are the same.
    # assert grid_search_opt.pending_configs == grid_search_tunables_grid


def test_grid_search(
    grid_search_opt: GridSearchOptimizer,
    grid_search_tunables: TunableGroups,
    grid_search_tunables_grid: List[Dict[str, TunableValue]],
) -> None:
    """Make sure that grid search optimizer initializes and works correctly."""
    score: Dict[str, TunableValue] = {"score": 1.0, "other_score": 2.0}
    status = Status.SUCCEEDED
    suggestion = grid_search_opt.suggest()
    suggestion_dict = suggestion.get_param_values()
    default_config = grid_search_tunables.restore_defaults().get_param_values()

    # First suggestion should be the defaults.
    assert suggestion.get_param_values() == default_config
    # But that shouldn't be the first element in the grid search.
    assert suggestion_dict != next(iter(grid_search_tunables_grid))
    # The suggestion should no longer be in the pending_configs.
    assert suggestion_dict not in grid_search_opt.pending_configs
    # But it should be in the suggested_configs now (and the only one).
    assert list(grid_search_opt.suggested_configs) == [default_config]

    # Register a score for that suggestion.
    grid_search_opt.register(suggestion, status, score)
    # Now it shouldn't be in the suggested_configs.
    assert len(list(grid_search_opt.suggested_configs)) == 0

    grid_search_tunables_grid.remove(default_config)
    assert default_config not in grid_search_opt.pending_configs
    assert all(config in grid_search_tunables_grid for config in grid_search_opt.pending_configs)
    assert all(
        config in list(grid_search_opt.pending_configs) for config in grid_search_tunables_grid
    )

    # The next suggestion should be a different element in the grid search.
    suggestion = grid_search_opt.suggest()
    suggestion_dict = suggestion.get_param_values()
    assert suggestion_dict != default_config
    assert suggestion_dict not in grid_search_opt.pending_configs
    assert suggestion_dict in grid_search_opt.suggested_configs
    grid_search_opt.register(suggestion, status, score)
    assert suggestion_dict not in grid_search_opt.pending_configs
    assert suggestion_dict not in grid_search_opt.suggested_configs

    grid_search_tunables_grid.remove(suggestion.get_param_values())
    assert all(config in grid_search_tunables_grid for config in grid_search_opt.pending_configs)
    assert all(
        config in list(grid_search_opt.pending_configs) for config in grid_search_tunables_grid
    )

    # We consider not_converged as either having reached "max_suggestions" or an empty grid?

    # Try to empty the rest of the grid.
    while grid_search_opt.not_converged():
        suggestion = grid_search_opt.suggest()
        grid_search_opt.register(suggestion, status, score)

    # The grid search should be empty now.
    assert not list(grid_search_opt.pending_configs)
    assert not list(grid_search_opt.suggested_configs)
    assert not grid_search_opt.not_converged()

    # But if we still have iterations left, we should be able to suggest again by
    # refilling the grid.
    assert grid_search_opt.current_iteration < grid_search_opt.max_iterations
    assert grid_search_opt.suggest()
    assert list(grid_search_opt.pending_configs)
    assert list(grid_search_opt.suggested_configs)
    assert grid_search_opt.not_converged()

    # Try to finish the rest of our iterations by repeating the grid.
    while grid_search_opt.not_converged():
        suggestion = grid_search_opt.suggest()
        grid_search_opt.register(suggestion, status, score)
    assert not grid_search_opt.not_converged()
    assert grid_search_opt.current_iteration >= grid_search_opt.max_iterations
    assert list(grid_search_opt.pending_configs)
    assert list(grid_search_opt.suggested_configs)


def test_grid_search_async_order(grid_search_opt: GridSearchOptimizer) -> None:
    """Make sure that grid search optimizer works correctly when suggest and register
    are called out of order.
    """
    # pylint: disable=too-many-locals
    score: Dict[str, TunableValue] = {"score": 1.0, "other_score": 2.0}
    status = Status.SUCCEEDED
    suggest_count = 10
    suggested = [grid_search_opt.suggest() for _ in range(suggest_count)]
    suggested_shuffled = suggested.copy()
    # Try to ensure the shuffled list is different.
    for _ in range(3):
        random.shuffle(suggested_shuffled)
        if suggested_shuffled != suggested:
            break
    assert suggested != suggested_shuffled

    for suggestion in suggested_shuffled:
        suggestion_dict = suggestion.get_param_values()
        assert suggestion_dict not in grid_search_opt.pending_configs
        assert suggestion_dict in grid_search_opt.suggested_configs
        grid_search_opt.register(suggestion, status, score)
        assert suggestion_dict not in grid_search_opt.suggested_configs

    best_score, best_config = grid_search_opt.get_best_observation()
    assert best_score == score

    # test re-register with higher score
    best_suggestion = suggested_shuffled[0]
    best_suggestion_dict = best_suggestion.get_param_values()
    assert best_suggestion_dict not in grid_search_opt.pending_configs
    assert best_suggestion_dict not in grid_search_opt.suggested_configs

    best_suggestion_score: Dict[str, TunableValue] = {}
    for opt_target, opt_dir in grid_search_opt.targets.items():
        val = score[opt_target]
        assert isinstance(val, (int, float))
        best_suggestion_score[opt_target] = val - 1 if opt_dir == "min" else val + 1

    grid_search_opt.register(best_suggestion, status, best_suggestion_score)
    assert best_suggestion_dict not in grid_search_opt.suggested_configs

    best_score, best_config = grid_search_opt.get_best_observation()
    assert best_score == best_suggestion_score
    assert best_config == best_suggestion

    # Check bulk register
    suggested = [grid_search_opt.suggest() for _ in range(suggest_count)]
    assert all(
        suggestion.get_param_values() not in grid_search_opt.pending_configs
        for suggestion in suggested
    )
    assert all(
        suggestion.get_param_values() in grid_search_opt.suggested_configs
        for suggestion in suggested
    )

    # Those new suggestions also shouldn't be in the set of previously suggested configs.
    assert all(suggestion.get_param_values() not in suggested_shuffled for suggestion in suggested)

    grid_search_opt.bulk_register(
        [suggestion.get_param_values() for suggestion in suggested],
        [score] * len(suggested),
        [status] * len(suggested),
    )

    assert all(
        suggestion.get_param_values() not in grid_search_opt.pending_configs
        for suggestion in suggested
    )
    assert all(
        suggestion.get_param_values() not in grid_search_opt.suggested_configs
        for suggestion in suggested
    )

    best_score, best_config = grid_search_opt.get_best_observation()
    assert best_score == best_suggestion_score
    assert best_config == best_suggestion


def test_grid_search_register(
    grid_search_opt: GridSearchOptimizer,
    grid_search_tunables: TunableGroups,
) -> None:
    """Make sure that the `.register()` method adjusts the score signs correctly."""
    assert grid_search_opt.register(
        grid_search_tunables,
        Status.SUCCEEDED,
        {
            "score": 1.0,
            "other_score": 2.0,
        },
    ) == {
        "score": -1.0,  # max
        "other_score": 2.0,  # min
    }

    assert grid_search_opt.register(grid_search_tunables, Status.FAILED) == {
        "score": float("inf"),
        "other_score": float("inf"),
    }
