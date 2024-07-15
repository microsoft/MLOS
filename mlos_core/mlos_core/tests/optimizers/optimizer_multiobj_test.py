#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Test multi-target optimization.
"""

import logging
from typing import List, Optional, Type

import pytest

import pandas as pd
import numpy as np
import ConfigSpace as CS

from mlos_core.optimizers import OptimizerType, BaseOptimizer

from mlos_core.tests import SEED

_LOG = logging.getLogger(__name__)


@pytest.mark.parametrize(('optimizer_class', 'kwargs'), [
    *[(member.value, {}) for member in OptimizerType],
])
def test_multi_target_opt_wrong_weights(optimizer_class: Type[BaseOptimizer], kwargs: dict) -> None:
    """
    Make sure that the optimizer raises an error if the number of objective weights
    does not match the number of optimization targets.
    """
    with pytest.raises(ValueError):
        optimizer_class(
            parameter_space=CS.ConfigurationSpace(seed=SEED),
            optimization_targets=['main_score', 'other_score'],
            objective_weights=[1],
            **kwargs
        )


@pytest.mark.parametrize(('objective_weights'), [
    [2, 1],
    [0.5, 0.5],
    None,
])
@pytest.mark.parametrize(('optimizer_class', 'kwargs'), [
    *[(member.value, {}) for member in OptimizerType],
])
def test_multi_target_opt(objective_weights: Optional[List[float]],
                          optimizer_class: Type[BaseOptimizer],
                          kwargs: dict) -> None:
    """
    Toy multi-target optimization problem to test the optimizers with
    mixed numeric types to ensure that original dtypes are retained.
    """
    max_iterations = 10

    def objective(point: pd.DataFrame) -> pd.DataFrame:
        # mix of hyperparameters, optimal is to select the highest possible
        return pd.DataFrame({
            "main_score": point.x + point.y,
            "other_score": point.x ** 2 + point.y ** 2,
        })

    input_space = CS.ConfigurationSpace(seed=SEED)
    # add a mix of numeric datatypes
    input_space.add_hyperparameter(
        CS.UniformIntegerHyperparameter(name='x', lower=0, upper=5))
    input_space.add_hyperparameter(
        CS.UniformFloatHyperparameter(name='y', lower=0.0, upper=5.0))

    optimizer = optimizer_class(
        parameter_space=input_space,
        optimization_targets=['main_score', 'other_score'],
        objective_weights=objective_weights,
        **kwargs,
    )

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_best_observations()

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_observations()

    for _ in range(max_iterations):
        suggestion, metadata = optimizer.suggest()
        assert isinstance(suggestion, pd.DataFrame)
        assert metadata is None or isinstance(metadata, pd.DataFrame)
        assert set(suggestion.columns) == {'x', 'y'}
        # Check suggestion values are the expected dtype
        assert isinstance(suggestion.x.iloc[0], np.integer)
        assert isinstance(suggestion.y.iloc[0], np.floating)
        # Check that suggestion is in the space
        test_configuration = CS.Configuration(
            optimizer.parameter_space, suggestion.astype('O').iloc[0].to_dict())
        # Raises an error if outside of configuration space
        test_configuration.is_valid_configuration()
        # Test registering the suggested configuration with a score.
        observation = objective(suggestion)
        assert isinstance(observation, pd.DataFrame)
        assert set(observation.columns) == {'main_score', 'other_score'}
        optimizer.register(configs=suggestion, scores=observation)

    (best_config, best_score, best_context) = optimizer.get_best_observations()
    assert isinstance(best_config, pd.DataFrame)
    assert isinstance(best_score, pd.DataFrame)
    assert best_context is None
    assert set(best_config.columns) == {'x', 'y'}
    assert set(best_score.columns) == {'main_score', 'other_score'}
    assert best_config.shape == (1, 2)
    assert best_score.shape == (1, 2)

    (all_configs, all_scores, all_contexts) = optimizer.get_observations()
    assert isinstance(all_configs, pd.DataFrame)
    assert isinstance(all_scores, pd.DataFrame)
    assert all_contexts is None
    assert set(all_configs.columns) == {'x', 'y'}
    assert set(all_scores.columns) == {'main_score', 'other_score'}
    assert all_configs.shape == (max_iterations, 2)
    assert all_scores.shape == (max_iterations, 2)
