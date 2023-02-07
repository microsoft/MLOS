"""
Tests for Bayesian Optimizers.
"""

# pylint: disable=missing-function-docstring

from typing import Type

import pytest

import pandas as pd
import numpy as np
import ConfigSpace as CS

from mlos_core.optimizers import (OptimizerType, OptimizerFactory,
    BaseOptimizer, EmukitOptimizer, SkoptOptimizer, RandomOptimizer)
from mlos_core.optimizers.bayesian_optimizers import BaseBayesianOptimizer
from mlos_core.spaces.adapters import SpaceAdapterType


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
    def objective(x):   # pylint: disable=invalid-name
        return (6 * x - 2)**2 * np.sin(12 * x - 4)
    # Emukit doesn't allow specifying a random state, so we set the global seed.
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


@pytest.mark.parametrize(('optimizer_type', 'kwargs'), [
    # Default optimizer
    (None, {}),
    # Enumerate all supported Optimizers
    *[(member, {}) for member in OptimizerType],
    # Optimizer with non-empty kwargs argument
    (OptimizerType.SKOPT, {'base_estimator': 'gp'}),
])
def test_create_optimizer_with_factory_method(optimizer_type: OptimizerType, kwargs):
    # Start defining a ConfigurationSpace for the Optimizer to search.
    input_space = CS.ConfigurationSpace(seed=1234)

    # Add a single continuous input dimension between 0 and 1.
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='x', lower=0, upper=1))

    if optimizer_type is None:
        optimizer = OptimizerFactory.create(input_space, optimizer_kwargs=kwargs)
    else:
        optimizer = OptimizerFactory.create(input_space, optimizer_type, optimizer_kwargs=kwargs)
    assert optimizer is not None

    assert optimizer.parameter_space is not None

    suggestion = optimizer.suggest()
    assert suggestion is not None

    if optimizer_type is not None:
        myrepr = repr(optimizer)
        assert myrepr.startswith(optimizer_type.value.__name__)


@pytest.mark.parametrize(('optimizer_type', 'kwargs'), [
    # Enumerate all supported Optimizers
    *[(member, {}) for member in OptimizerType],
    # Optimizer with non-empty kwargs argument
    (OptimizerType.SKOPT, {'base_estimator': 'gp'}),
])
def test_optimizer_with_llamatune(optimizer_type: OptimizerType, kwargs):
    def objective(point):   # pylint: disable=invalid-name
        # Best value can be reached by tuning an 1-dimensional search space
        return np.sin(point['x'] * point['y'])

    input_space = CS.ConfigurationSpace(seed=1234)
    # Add two continuous inputs
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='x', lower=0, upper=3))
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='y', lower=0, upper=3))

    # Initialize optimizer
    optimizer = OptimizerFactory.create(input_space, optimizer_type, optimizer_kwargs=kwargs)
    assert optimizer is not None

    # Initialize another optimizer that uses LlamaTune space adapter
    space_adapter_kwargs = dict(
        num_low_dims=1,
        special_param_values=None,
        max_unique_values_per_param=None,
    )
    llamatune_optimizer = OptimizerFactory.create(
        input_space,
        optimizer_type,
        optimizer_kwargs=kwargs,
        space_adapter_type=SpaceAdapterType.LLAMATUNE,
        space_adapter_kwargs=space_adapter_kwargs
    )
    assert llamatune_optimizer is not None

    num_iters = 50
    for _ in range(num_iters):
        # loop for optimizer
        suggestion = optimizer.suggest()
        observation = objective(suggestion)
        optimizer.register(suggestion, observation)

        # loop for llamatune-optimizer
        suggestion = llamatune_optimizer.suggest()
        assert suggestion['x'].iloc[0] == suggestion['y'].iloc[0]   # optimizer explores 1-dimensional space
        observation = objective(suggestion)
        llamatune_optimizer.register(suggestion, observation)

    # Retrieve best observations
    best_observation = optimizer.get_best_observation()
    llamatune_best_observation = llamatune_optimizer.get_best_observation()

    for best_obv in (best_observation, llamatune_best_observation):
        assert isinstance(best_obv, pd.DataFrame)
        assert (best_obv.columns == ['x', 'y', 'score']).all()

    # LlamaTune's optimizer score should better (i.e., lower) than plain optimizer's one, or close to that
    assert best_observation['score'].iloc[0] > llamatune_best_observation['score'].iloc[0] or \
        best_observation['score'].iloc[0] + 1e-3 > llamatune_best_observation['score'].iloc[0]

    # Retrieve and check all observations
    for all_obvs in (optimizer.get_observations(), llamatune_optimizer.get_observations()):
        assert isinstance(all_obvs, pd.DataFrame)
        assert all_obvs.shape == (num_iters, 3)
        assert (all_obvs.columns == ['x', 'y', 'score']).all()

    # .surrogate_predict method not currently implemented if space adapter is employed
    if isinstance(optimizer, BaseBayesianOptimizer):
        with pytest.raises(NotImplementedError):
            _ = llamatune_optimizer.surrogate_predict(llamatune_best_observation[['x']])
