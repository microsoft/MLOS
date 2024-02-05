#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for Bayesian Optimizers.
"""

from copy import deepcopy
from typing import List, Optional, Type

import logging
import pytest

import pandas as pd
import numpy as np
import numpy.typing as npt
import ConfigSpace as CS

from mlos_core.optimizers import (
    OptimizerType, ConcreteOptimizer, OptimizerFactory, BaseOptimizer)

from mlos_core.optimizers.bayesian_optimizers import BaseBayesianOptimizer, SmacOptimizer
from mlos_core.spaces.adapters import SpaceAdapterType

from mlos_core.tests import get_all_concrete_subclasses


_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


@pytest.mark.parametrize(('optimizer_class', 'kwargs'), [
    *[(member.value, {}) for member in OptimizerType],
])
def test_create_optimizer_and_suggest(configuration_space: CS.ConfigurationSpace,
                                      optimizer_class: Type[BaseOptimizer], kwargs: Optional[dict]) -> None:
    """
    Test that we can create an optimizer and get a suggestion from it.
    """
    if kwargs is None:
        kwargs = {}
    optimizer = optimizer_class(parameter_space=configuration_space, **kwargs)
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
])
def test_basic_interface_toy_problem(configuration_space: CS.ConfigurationSpace,
                                     optimizer_class: Type[BaseOptimizer], kwargs: Optional[dict]) -> None:
    """
    Toy problem to test the optimizers.
    """
    max_iterations = 20
    if kwargs is None:
        kwargs = {}
    if optimizer_class == OptimizerType.SMAC.value:
        # SMAC sets the initial random samples as a percentage of the max iterations, which defaults to 100.
        # To avoid having to train more than 25 model iterations, we set a lower number of max iterations.
        kwargs['max_trials'] = max_iterations * 2

    def objective(x: pd.Series) -> npt.ArrayLike:   # pylint: disable=invalid-name
        ret: npt.ArrayLike = (6 * x - 2)**2 * np.sin(12 * x - 4)
        return ret
    # Emukit doesn't allow specifying a random state, so we set the global seed.
    np.random.seed(42)
    optimizer = optimizer_class(parameter_space=configuration_space, **kwargs)

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_best_observation()

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_observations()

    for _ in range(max_iterations):
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
])
def test_create_optimizer_with_factory_method(configuration_space: CS.ConfigurationSpace,
                                              optimizer_type: Optional[OptimizerType], kwargs: Optional[dict]) -> None:
    """
    Test that we can create an optimizer via a factory.
    """
    if kwargs is None:
        kwargs = {}
    if optimizer_type is None:
        optimizer = OptimizerFactory.create(
            parameter_space=configuration_space,
            optimizer_kwargs=kwargs,
        )
    else:
        optimizer = OptimizerFactory.create(
            parameter_space=configuration_space,
            optimizer_type=optimizer_type,
            optimizer_kwargs=kwargs,
        )
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
    (OptimizerType.SMAC, {
        # Test with default config.
        'use_default_config': True,
        # 'n_random_init': 10,
    }),
])
def test_optimizer_with_llamatune(optimizer_type: OptimizerType, kwargs: Optional[dict]) -> None:
    """
    Toy problem to test the optimizers with llamatune space adapter.
    """
    # pylint: disable=too-complex
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-locals
    num_iters = 50
    if kwargs is None:
        kwargs = {}

    def objective(point: pd.DataFrame) -> pd.Series:
        # Best value can be reached by tuning an 1-dimensional search space
        ret: pd.Series = np.sin(point['x'] * point['y'])
        assert ret.hasnans is False
        return ret

    input_space = CS.ConfigurationSpace(seed=1234)
    # Add two continuous inputs
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='x', lower=0, upper=3))
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='y', lower=0, upper=3))

    # Initialize an optimizer that uses LlamaTune space adapter
    space_adapter_kwargs = {
        "num_low_dims": 1,
        "special_param_values": None,
        "max_unique_values_per_param": None,
    }

    # Make some adjustments to the kwargs for the optimizer and LlamaTuned
    # optimizer for debug/testing.

    # if optimizer_type == OptimizerType.SMAC:
    #    # Allow us to override the number of random init samples.
    #    kwargs['max_ratio'] = 1.0
    optimizer_kwargs = deepcopy(kwargs)
    llamatune_optimizer_kwargs = deepcopy(kwargs)
    # if optimizer_type == OptimizerType.SMAC:
    #    optimizer_kwargs['n_random_init'] = 20
    #    llamatune_optimizer_kwargs['n_random_init'] = 10

    llamatune_optimizer: BaseOptimizer = OptimizerFactory.create(
        parameter_space=input_space,
        optimizer_type=optimizer_type,
        optimizer_kwargs=llamatune_optimizer_kwargs,
        space_adapter_type=SpaceAdapterType.LLAMATUNE,
        space_adapter_kwargs=space_adapter_kwargs,
    )
    # Initialize an optimizer that uses the original space
    optimizer: BaseOptimizer = OptimizerFactory.create(
        parameter_space=input_space,
        optimizer_type=optimizer_type,
        optimizer_kwargs=optimizer_kwargs,
    )
    assert optimizer is not None
    assert llamatune_optimizer is not None
    assert optimizer.optimizer_parameter_space != llamatune_optimizer.optimizer_parameter_space

    llamatune_n_random_init = 0
    opt_n_random_init = int(kwargs.get('n_random_init', 0))
    if optimizer_type == OptimizerType.SMAC:
        assert isinstance(optimizer, SmacOptimizer)
        assert isinstance(llamatune_optimizer, SmacOptimizer)
        opt_n_random_init = optimizer.n_random_init
        llamatune_n_random_init = llamatune_optimizer.n_random_init

    for i in range(num_iters):
        # Place to set a breakpoint for when the optimizer is done with random init.
        if llamatune_n_random_init and i > llamatune_n_random_init:
            _LOG.debug("LlamaTuned Optimizer is done with random init.")
        if opt_n_random_init and i >= opt_n_random_init:
            _LOG.debug("Optimizer is done with random init.")

        # loop for optimizer
        suggestion = optimizer.suggest()
        observation = objective(suggestion)
        optimizer.register(suggestion, observation)

        # loop for llamatune-optimizer
        suggestion = llamatune_optimizer.suggest()
        _x, _y = suggestion['x'].iloc[0], suggestion['y'].iloc[0]
        assert _x == pytest.approx(_y, rel=1e-3) or _x + _y == pytest.approx(3., rel=1e-3)  # optimizer explores 1-dimensional space
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
            llamatune_optimizer.surrogate_predict(llamatune_best_observation[['x', 'y']])


# Dynamically determine all of the optimizers we have implemented.
# Note: these must be sorted.
optimizer_subclasses: List[Type[BaseOptimizer]] = get_all_concrete_subclasses(BaseOptimizer,  # type: ignore[type-abstract]
                                                                              pkg_name='mlos_core')
assert optimizer_subclasses


@pytest.mark.parametrize(('optimizer_class'), optimizer_subclasses)
def test_optimizer_type_defs(optimizer_class: Type[BaseOptimizer]) -> None:
    """
    Test that all optimizer classes are listed in the OptimizerType enum.
    """
    optimizer_type_classes = {member.value for member in OptimizerType}
    assert optimizer_class in optimizer_type_classes


@pytest.mark.parametrize(('optimizer_type', 'kwargs'), [
    # Enumerate all supported Optimizers
    *[(member, {}) for member in OptimizerType],
    # Optimizer with non-empty kwargs argument
    (OptimizerType.SMAC, {
        # Test with default config.
        'use_default_config': True,
        # 'n_random_init': 10,
    }),
])
def test_mixed_input_space_types(optimizer_type: OptimizerType, kwargs: Optional[dict]) -> None:
    """
    Toy problem to test the optimizers.
    """
    max_iterations = 10
    if kwargs is None:
        kwargs = {}

    def objective(point: pd.DataFrame) -> pd.Series:
        # mix of hyperparameters, optimal is to select the highest possible
        ret: pd.Series = point["x"] + point["y"]
        return ret

    input_space = CS.ConfigurationSpace(seed=2169)
    # add a mix of numeric datatypes
    input_space.add_hyperparameter(CS.UniformIntegerHyperparameter(name='x', lower=0, upper=5))
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='y', lower=0.0, upper=5.0))

    optimizer: BaseOptimizer = OptimizerFactory.create(
        parameter_space=input_space,
        optimizer_type=optimizer_type,
        optimizer_kwargs=kwargs,
    )

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_best_observation()

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_observations()

    for _ in range(max_iterations):
        suggestion = optimizer.suggest()
        assert isinstance(suggestion, pd.DataFrame)
        assert (suggestion.columns == ['x', 'y']).all()
        # check that suggestion is in the space
        configuration = CS.Configuration(optimizer.parameter_space, suggestion.iloc[0].to_dict())
        # Raises an error if outside of configuration space
        configuration.is_valid_configuration()
        observation = objective(suggestion)
        assert isinstance(observation, pd.Series)
        optimizer.register(suggestion, observation)

    best_observation = optimizer.get_best_observation()
    assert isinstance(best_observation, pd.DataFrame)

    all_observations = optimizer.get_observations()
    assert isinstance(all_observations, pd.DataFrame)
