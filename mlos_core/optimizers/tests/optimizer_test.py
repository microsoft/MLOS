"""
Tests for Bayesian Optimizers.
"""

# pylint: disable=missing-function-docstring

from typing import Type

import pytest

import pandas as pd
import numpy as np
import ConfigSpace as CS

from mlos_core.optimizers import BaseOptimizer, EmukitOptimizer, SkoptOptimizer, RandomOptimizer
from mlos_core.optimizers.bayesian_optimizers import BaseBayesianOptimizer


@pytest.mark.parametrize(('optimizer_class', 'kwargs'), [
    (EmukitOptimizer, {}),
    (SkoptOptimizer, {'base_estimator': 'gp'}),
    (RandomOptimizer, {})
])
def test_create_optimizer_and_suggest(optimizer_class: Type[BaseOptimizer], kwargs):
    # Start defining a ConfigurationSpace for the Optimizer to search.
    input_space = CS.ConfigurationSpace(seed=1234)

    # Add a single continuous input dimension between 0 and 1.
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='x', lower=0, upper=1))

    optimizer = optimizer_class(input_space, **kwargs)
    assert optimizer is not None

    assert optimizer.parameter_space is not None

    suggestion = optimizer.suggest()
    assert suggestion is not None

    myrepr = repr(optimizer)
    assert myrepr.startswith(optimizer_class.__name__)

    # pending not implemented
    with pytest.raises(NotImplementedError):
        optimizer.register_pending(suggestion)


@pytest.mark.parametrize(('optimizer_class', 'kwargs'), [
    (EmukitOptimizer, {}),
    (SkoptOptimizer, {'base_estimator': 'gp'}),
    (SkoptOptimizer, {'base_estimator': 'et'}),
    (RandomOptimizer, {})
])
def test_basic_interface_toy_problem(optimizer_class: Type[BaseOptimizer], kwargs):
    def objective(x):
        return (6*x-2)**2*np.sin(12*x-4)
    # Emukit doesn't allow specifing a random state, so we set the global seed.
    np.random.seed(42)

    # Start defining a ConfigurationSpace for the Optimizer to search.
    input_space = CS.ConfigurationSpace(seed=1234)

    # Add a single continuous input dimension between 0 and 1.
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='x', lower=0, upper=1))

    optimizer = optimizer_class(input_space, **kwargs)

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_best_observation()

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_observations()

    for _ in range(20):
        suggestion = optimizer.suggest()
        assert isinstance(suggestion, pd.DataFrame)
        assert suggestion.columns == ['x']
        # check that suggestion is in the space
        configuration = CS.Configuration(optimizer.parameter_space, suggestion.iloc[0].to_dict())
        # Raises an error if outside of configuration space
        configuration.is_valid_configuration()
        observation = objective(suggestion['x'])
        assert isinstance(observation, pd.Series)
        optimizer.register(suggestion, observation)

    best_observation = optimizer.get_best_observation()
    assert isinstance(best_observation, pd.DataFrame)
    assert (best_observation.columns == ['x', 'score']).all()
    assert best_observation['score'].iloc[0] < -5

    all_observations = optimizer.get_observations()
    assert isinstance(all_observations, pd.DataFrame)
    assert all_observations.shape == (20, 2)
    assert (all_observations.columns == ['x', 'score']).all()

    # It would be better to put this into bayesian_optimizer_test but then we'd have to refit the model
    if isinstance(optimizer, BaseBayesianOptimizer):
        pred_best = optimizer.surrogate_predict(best_observation[['x']])
        assert pred_best.shape == (1,)

        pred_all = optimizer.surrogate_predict(all_observations[['x']])
        assert pred_all.shape == (20,)
