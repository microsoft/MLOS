#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Test multi-target optimization."""

import logging
from typing import List, Optional, Type

import ConfigSpace as CS
import pandas as pd
import pytest

from mlos_core.data_classes import Observations, Suggestion
from mlos_core.optimizers import BaseOptimizer, OptimizerType
from mlos_core.tests import SEED

_LOG = logging.getLogger(__name__)


@pytest.mark.parametrize(
    ("optimizer_class", "kwargs"),
    [
        *[(member.value, {}) for member in OptimizerType],
    ],
)
def test_multi_target_opt_wrong_weights(
    optimizer_class: Type[BaseOptimizer],
    kwargs: dict,
) -> None:
    """Make sure that the optimizer raises an error if the number of objective weights
    does not match the number of optimization targets.
    """
    with pytest.raises(ValueError):
        optimizer_class(
            parameter_space=CS.ConfigurationSpace(seed=SEED),
            optimization_targets=["main_score", "other_score"],
            objective_weights=[1],
            **kwargs,
        )


@pytest.mark.parametrize(
    ("objective_weights"),
    [
        [2, 1],
        [0.5, 0.5],
        None,
    ],
)
@pytest.mark.parametrize(
    ("optimizer_class", "kwargs"),
    [
        *[(member.value, {}) for member in OptimizerType],
    ],
)
def test_multi_target_opt(
    objective_weights: Optional[List[float]],
    optimizer_class: Type[BaseOptimizer],
    kwargs: dict,
) -> None:
    """Toy multi-target optimization problem to test the optimizers with mixed numeric
    types to ensure that original dtypes are retained.
    """
    # pylint: disable=too-many-locals
    max_iterations = 10

    def objective(point: pd.Series) -> pd.Series:
        # mix of hyperparameters, optimal is to select the highest possible
        ret: pd.Series = pd.Series(
            {
                "main_score": point.x + point.y,
                "other_score": point.x**2 + point.y**2,
            }
        )
        return ret

    input_space = CS.ConfigurationSpace(seed=SEED)
    # add a mix of numeric datatypes
    input_space.add(CS.UniformIntegerHyperparameter(name="x", lower=0, upper=5))
    input_space.add(CS.UniformFloatHyperparameter(name="y", lower=0.0, upper=5.0))

    optimizer = optimizer_class(
        parameter_space=input_space,
        optimization_targets=["main_score", "other_score"],
        objective_weights=objective_weights,
        **kwargs,
    )

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_best_observations()

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_observations()

    for _ in range(max_iterations):
        suggestion = optimizer.suggest()
        assert isinstance(suggestion, Suggestion)
        assert isinstance(suggestion.config, pd.Series)
        assert suggestion.metadata is None or isinstance(suggestion.metadata, pd.Series)
        assert set(suggestion.config.index) == {"x", "y"}
        # Check suggestion values are the expected dtype
        assert isinstance(suggestion.config["x"], int)
        assert isinstance(suggestion.config["y"], float)
        # Check that suggestion is in the space
        config_dict: dict = suggestion.config.to_dict()
        test_configuration = CS.Configuration(optimizer.parameter_space, config_dict)
        # Raises an error if outside of configuration space
        test_configuration.check_valid_configuration()
        # Test registering the suggested configuration with a score.
        observation = objective(suggestion.config)
        assert isinstance(observation, pd.Series)
        assert set(observation.index) == {"main_score", "other_score"}
        optimizer.register(observations=suggestion.complete(observation))

    best_observations = optimizer.get_best_observations()
    assert isinstance(best_observations, Observations)
    assert isinstance(best_observations.configs, pd.DataFrame)
    assert isinstance(best_observations.scores, pd.DataFrame)
    assert best_observations.contexts is None
    assert set(best_observations.configs.columns) == {"x", "y"}
    assert set(best_observations.scores.columns) == {"main_score", "other_score"}
    assert best_observations.configs.shape == (1, 2)
    assert best_observations.scores.shape == (1, 2)

    all_observations = optimizer.get_observations()
    assert isinstance(all_observations, Observations)
    assert isinstance(all_observations.configs, pd.DataFrame)
    assert isinstance(all_observations.scores, pd.DataFrame)
    assert all_observations.contexts is None
    assert set(all_observations.configs.columns) == {"x", "y"}
    assert set(all_observations.scores.columns) == {"main_score", "other_score"}
    assert all_observations.configs.shape == (max_iterations, 2)
    assert all_observations.scores.shape == (max_iterations, 2)
