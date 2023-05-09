#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for Bayesian Optimizers.
"""

from typing import List, Optional, Type

import pytest

import pandas as pd
import numpy as np
import numpy.typing as npt
import ConfigSpace as CS

from mlos_core.optimizers import (
    OptimizerType, ConcreteOptimizer, OptimizerFactory, BaseOptimizer,
    SkoptOptimizer)

from mlos_core.optimizers.bayesian_optimizers import BaseBayesianOptimizer
from mlos_core.spaces.adapters import SpaceAdapterType

from mlos_core.tests import get_all_concrete_subclasses


@pytest.mark.parametrize(('optimizer_class', 'kwargs'), [
    *[(member.value, {}) for member in OptimizerType],
    (SkoptOptimizer, {'base_estimator': 'gp'}),
])
def test_create_optimizer_and_suggest(configuration_space: CS.ConfigurationSpace,
                                      optimizer_class: Type[BaseOptimizer], kwargs: Optional[dict]) -> None:
    """
    Test that we can create an optimizer and get a suggestion from it.
    """
    if kwargs is None:
        kwargs = {}
    optimizer = optimizer_class(configuration_space, **kwargs)
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
    *[(member.value, {}) for member in OptimizerType],
    (SkoptOptimizer, {'base_estimator': 'gp', 'seed': 42}),
    (SkoptOptimizer, {'base_estimator': 'et', 'seed': 42}),
])
def test_basic_interface_toy_problem(configuration_space: CS.ConfigurationSpace,
                                     optimizer_class: Type[BaseOptimizer], kwargs: Optional[dict]) -> None:
    """
    Toy problem to test the optimizers.
    """
    if kwargs is None:
        kwargs = {}

    def objective(x: pd.Series) -> npt.ArrayLike:   # pylint: disable=invalid-name
        ret: npt.ArrayLike = (6 * x - 2)**2 * np.sin(12 * x - 4)
        return ret
    # Emukit doesn't allow specifying a random state, so we set the global seed.
    np.random.seed(42)
    optimizer = optimizer_class(configuration_space, **kwargs)

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_best_observation()

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_observations()

    for _ in range(20):
        suggestion = optimizer.suggest()
        assert isinstance(suggestion, pd.DataFrame)
        assert (suggestion.columns == ['x', 'y', 'z']).all()
        # check that suggestion is in the space
        configuration = CS.Configuration(optimizer.parameter_space, suggestion.iloc[0].to_dict())
        # Raises an error if outside of configuration space
        configuration.is_valid_configuration()
        observation = objective(suggestion['x'])
        assert isinstance(observation, pd.Series)
        optimizer.register(suggestion, observation)

    best_observation = optimizer.get_best_observation()
    assert isinstance(best_observation, pd.DataFrame)
    assert (best_observation.columns == ['x', 'y', 'z', 'score']).all()
    assert best_observation['score'].iloc[0] < -5

    all_observations = optimizer.get_observations()
    assert isinstance(all_observations, pd.DataFrame)
    assert all_observations.shape == (20, 4)
    assert (all_observations.columns == ['x', 'y', 'z', 'score']).all()

    # It would be better to put this into bayesian_optimizer_test but then we'd have to refit the model
    if isinstance(optimizer, BaseBayesianOptimizer):
        pred_best = optimizer.surrogate_predict(best_observation[['x', 'y', 'z']])
        assert pred_best.shape == (1,)

        pred_all = optimizer.surrogate_predict(all_observations[['x', 'y', 'z']])
        assert pred_all.shape == (20,)


@pytest.mark.parametrize(('optimizer_type'), [
    # Enumerate all supported Optimizers
    # *[member for member in OptimizerType],
    *list(OptimizerType),
])
def test_concrete_optimizer_type(optimizer_type: OptimizerType) -> None:
    """
    Test that all optimizer types are listed in the ConcreteOptimizer constraints.
    """
    assert optimizer_type.value in ConcreteOptimizer.__constraints__    # type: ignore[attr-defined]  # pylint: disable=no-member


@pytest.mark.parametrize(('optimizer_type', 'kwargs'), [
    # Default optimizer
    (None, {}),
    # Enumerate all supported Optimizers
    *[(member, {}) for member in OptimizerType],
    # Optimizer with non-empty kwargs argument
    (OptimizerType.SKOPT, {'base_estimator': 'gp'}),
])
def test_create_optimizer_with_factory_method(configuration_space: CS.ConfigurationSpace,
                                              optimizer_type: Optional[OptimizerType], kwargs: Optional[dict]) -> None:
    """
    Test that we can create an optimizer via a factory.
    """
    if kwargs is None:
        kwargs = {}
    if optimizer_type is None:
        optimizer = OptimizerFactory.create(configuration_space, optimizer_kwargs=kwargs)
    else:
        optimizer = OptimizerFactory.create(configuration_space, optimizer_type, optimizer_kwargs=kwargs)
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
    (OptimizerType.SKOPT, {'base_estimator': 'gp', 'seed': 42}),
])
def test_optimizer_with_llamatune(optimizer_type: OptimizerType, kwargs: Optional[dict]) -> None:
    """
    Toy problem to test the optimizers with llamatune space adapter.
    """
    if kwargs is None:
        kwargs = {}

    def objective(point: pd.DataFrame) -> pd.Series:   # pylint: disable=invalid-name
        # Best value can be reached by tuning an 1-dimensional search space
        ret: pd.Series = np.sin(point['x'] * point['y'])
        return ret

    input_space = CS.ConfigurationSpace(seed=1234)
    # Add two continuous inputs
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='x', lower=0, upper=3))
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='y', lower=0, upper=3))

    # Initialize optimizer
    optimizer: BaseOptimizer = OptimizerFactory.create(input_space, optimizer_type, optimizer_kwargs=kwargs)
    assert optimizer is not None

    # Initialize another optimizer that uses LlamaTune space adapter
    space_adapter_kwargs = {
        "num_low_dims": 1,
        "special_param_values": None,
        "max_unique_values_per_param": None,
    }
    llamatune_optimizer: BaseOptimizer = OptimizerFactory.create(
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
    if isinstance(llamatune_optimizer, BaseBayesianOptimizer):
        with pytest.raises(NotImplementedError):
            _ = llamatune_optimizer.surrogate_predict(llamatune_best_observation[['x']])


# Dynamically determine all of the optimizers we have implemented.
# Note: these must be sorted.
optimizer_subclasses: List[Type[BaseOptimizer]] = get_all_concrete_subclasses(BaseOptimizer)  # type: ignore[type-abstract]
assert optimizer_subclasses


@pytest.mark.parametrize(('optimizer_class'), optimizer_subclasses)
def test_optimizer_type_defs(optimizer_class: Type[BaseOptimizer]) -> None:
    """
    Test that all optimizer classes are listed in the OptimizerType enum.
    """
    optimizer_type_classes = {member.value for member in OptimizerType}
    assert optimizer_class in optimizer_type_classes
