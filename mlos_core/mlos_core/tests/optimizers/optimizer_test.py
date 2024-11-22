#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for Bayesian Optimizers."""

import logging
from copy import deepcopy
from typing import Any, List, Optional, Type

import ConfigSpace as CS
import numpy as np
import pandas as pd
import pytest

from mlos_core.data_classes import Observations, Suggestion
from mlos_core.optimizers import (
    BaseOptimizer,
    ConcreteOptimizer,
    OptimizerFactory,
    OptimizerType,
)
from mlos_core.optimizers.bayesian_optimizers import (
    BaseBayesianOptimizer,
    SmacOptimizer,
)
from mlos_core.spaces.adapters import SpaceAdapterType
from mlos_core.tests import SEED, get_all_concrete_subclasses

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


@pytest.mark.parametrize(
    ("optimizer_class", "kwargs"),
    [
        *[(member.value, {}) for member in OptimizerType],
    ],
)
def test_create_optimizer_and_suggest(
    configuration_space: CS.ConfigurationSpace,
    optimizer_class: Type[BaseOptimizer],
    kwargs: Optional[dict],
) -> None:
    """Test that we can create an optimizer and get a suggestion from it."""
    if kwargs is None:
        kwargs = {}
    optimizer = optimizer_class(
        parameter_space=configuration_space,
        optimization_targets=["score"],
        **kwargs,
    )
    assert optimizer is not None

    assert optimizer.parameter_space is not None

    suggestion = optimizer.suggest()
    assert suggestion is not None

    myrepr = repr(optimizer)
    assert myrepr.startswith(optimizer_class.__name__)

    # pending not implemented
    with pytest.raises(NotImplementedError):
        optimizer.register_pending(pending=suggestion)


@pytest.mark.parametrize(
    ("optimizer_class", "kwargs"),
    [
        *[(member.value, {}) for member in OptimizerType],
    ],
)
def test_basic_interface_toy_problem(
    configuration_space: CS.ConfigurationSpace,
    optimizer_class: Type[BaseOptimizer],
    kwargs: Optional[dict],
) -> None:
    """Toy problem to test the optimizers."""
    # pylint: disable=too-many-locals
    max_iterations = 20
    if kwargs is None:
        kwargs = {}
    if optimizer_class == OptimizerType.SMAC.value:
        # SMAC sets the initial random samples as a percentage of the max
        # iterations, which defaults to 100.
        # To avoid having to train more than 25 model iterations, we set a lower
        # number of max iterations.
        kwargs["max_trials"] = max_iterations * 2

    def objective(inp: float) -> pd.Series:
        series: pd.Series = pd.Series(
            {"score": (6 * inp - 2) ** 2 * np.sin(12 * inp - 4)}
        )  # needed for type hinting
        return series

    # Emukit doesn't allow specifying a random state, so we set the global seed.
    np.random.seed(SEED)
    optimizer = optimizer_class(
        parameter_space=configuration_space,
        optimization_targets=["score"],
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
        assert set(suggestion.config.index) == {"x", "y", "z"}
        # check that suggestion is in the space
        dict_config: dict = suggestion.config.to_dict()
        configuration = CS.Configuration(optimizer.parameter_space, dict_config)
        # Raises an error if outside of configuration space
        configuration.check_valid_configuration()
        inp: Any = suggestion.config["x"]
        assert isinstance(inp, (int, float))
        observation = objective(inp)
        assert isinstance(observation, pd.Series)
        optimizer.register(observations=suggestion.complete(observation))

    best_observation = optimizer.get_best_observations()
    assert isinstance(best_observation, Observations)
    assert isinstance(best_observation.configs, pd.DataFrame)
    assert isinstance(best_observation.scores, pd.DataFrame)
    assert best_observation.contexts is None
    assert set(best_observation.configs.columns) == {"x", "y", "z"}
    assert set(best_observation.scores.columns) == {"score"}
    assert best_observation.configs.shape == (1, 3)
    assert best_observation.scores.shape == (1, 1)
    assert best_observation.scores.score.iloc[0] < -4

    all_observations = optimizer.get_observations()
    assert isinstance(all_observations, Observations)
    assert isinstance(all_observations.configs, pd.DataFrame)
    assert isinstance(all_observations.scores, pd.DataFrame)
    assert all_observations.contexts is None
    assert set(all_observations.configs.columns) == {"x", "y", "z"}
    assert set(all_observations.scores.columns) == {"score"}
    assert all_observations.configs.shape == (20, 3)
    assert all_observations.scores.shape == (20, 1)

    # It would be better to put this into bayesian_optimizer_test but then we'd have
    # to refit the model
    if isinstance(optimizer, BaseBayesianOptimizer):
        pred_best = [
            optimizer.surrogate_predict(suggestion=observation.to_suggestion())
            for observation in best_observation
        ]
        assert len(pred_best) == 1

        pred_all = [
            optimizer.surrogate_predict(suggestion=observation.to_suggestion())
            for observation in all_observations
        ]
        assert len(pred_all) == 20


@pytest.mark.parametrize(
    ("optimizer_type"),
    [
        # Enumerate all supported Optimizers
        # *[member for member in OptimizerType],
        *list(OptimizerType),
    ],
)
def test_concrete_optimizer_type(optimizer_type: OptimizerType) -> None:
    """Test that all optimizer types are listed in the ConcreteOptimizer constraints."""
    # pylint: disable=no-member
    assert optimizer_type.value in ConcreteOptimizer.__constraints__


@pytest.mark.parametrize(
    ("optimizer_type", "kwargs"),
    [
        # Default optimizer
        (None, {}),
        # Enumerate all supported Optimizers
        *[(member, {}) for member in OptimizerType],
        # Optimizer with non-empty kwargs argument
    ],
)
def test_create_optimizer_with_factory_method(
    configuration_space: CS.ConfigurationSpace,
    optimizer_type: Optional[OptimizerType],
    kwargs: Optional[dict],
) -> None:
    """Test that we can create an optimizer via a factory."""
    if kwargs is None:
        kwargs = {}
    if optimizer_type is None:
        optimizer = OptimizerFactory.create(
            parameter_space=configuration_space,
            optimization_targets=["score"],
            optimizer_kwargs=kwargs,
        )
    else:
        optimizer = OptimizerFactory.create(
            parameter_space=configuration_space,
            optimization_targets=["score"],
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


@pytest.mark.parametrize(
    ("optimizer_type", "kwargs"),
    [
        # Enumerate all supported Optimizers
        *[(member, {}) for member in OptimizerType],
        # Optimizer with non-empty kwargs argument
        (
            OptimizerType.SMAC,
            {
                # Test with default config.
                "use_default_config": True,
                # 'n_random_init': 10,
            },
        ),
    ],
)
def test_optimizer_with_llamatune(optimizer_type: OptimizerType, kwargs: Optional[dict]) -> None:
    """Toy problem to test the optimizers with llamatune space adapter."""
    # pylint: disable=too-complex,disable=too-many-statements,disable=too-many-locals
    num_iters = 50
    if kwargs is None:
        kwargs = {}

    def objective(point: pd.Series) -> pd.Series:
        # Best value can be reached by tuning an 1-dimensional search space
        ret: pd.Series = pd.Series({"score": np.sin(point.x * point.y)})
        assert pd.notna(ret.score)
        return ret

    input_space = CS.ConfigurationSpace(seed=1234)
    # Add two continuous inputs
    input_space.add(CS.UniformFloatHyperparameter(name="x", lower=0, upper=3))
    input_space.add(CS.UniformFloatHyperparameter(name="y", lower=0, upper=3))

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
        optimization_targets=["score"],
        optimizer_type=optimizer_type,
        optimizer_kwargs=llamatune_optimizer_kwargs,
        space_adapter_type=SpaceAdapterType.LLAMATUNE,
        space_adapter_kwargs=space_adapter_kwargs,
    )
    # Initialize an optimizer that uses the original space
    optimizer: BaseOptimizer = OptimizerFactory.create(
        parameter_space=input_space,
        optimization_targets=["score"],
        optimizer_type=optimizer_type,
        optimizer_kwargs=optimizer_kwargs,
    )
    assert optimizer is not None
    assert llamatune_optimizer is not None
    assert optimizer.optimizer_parameter_space != llamatune_optimizer.optimizer_parameter_space

    llamatune_n_random_init = 0
    opt_n_random_init = int(kwargs.get("n_random_init", 0))
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
        observation = objective(suggestion.config)
        optimizer.register(observations=suggestion.complete(observation))

        # loop for llamatune-optimizer
        suggestion = llamatune_optimizer.suggest()
        _x, _y = suggestion.config["x"], suggestion.config["y"]
        # optimizer explores 1-dimensional space
        assert _x == pytest.approx(_y, rel=1e-3) or _x + _y == pytest.approx(3.0, rel=1e-3)
        observation = objective(suggestion.config)
        llamatune_optimizer.register(observations=suggestion.complete(observation))

    # Retrieve best observations
    best_observation: Observations = optimizer.get_best_observations()
    assert isinstance(best_observation, Observations)
    llamatune_best_observations: Observations = llamatune_optimizer.get_best_observations()
    assert isinstance(llamatune_best_observations, Observations)

    for observations in (best_observation, llamatune_best_observations):
        assert isinstance(observations.configs, pd.DataFrame)
        assert isinstance(observations.scores, pd.DataFrame)
        assert observations.contexts is None
        assert set(observations.configs.columns) == {"x", "y"}
        assert set(observations.scores.columns) == {"score"}

    # LlamaTune's optimizer score should better (i.e., lower) than plain optimizer's
    # one, or close to that
    assert (
        best_observation.scores.score.iloc[0] > llamatune_best_observations.scores.score.iloc[0]
        or best_observation.scores.score.iloc[0] + 1e-3
        > llamatune_best_observations.scores.score.iloc[0]
    )

    # Retrieve and check all observations
    for all_observations in (
        optimizer.get_observations(),
        llamatune_optimizer.get_observations(),
    ):
        assert isinstance(all_observations.configs, pd.DataFrame)
        assert isinstance(all_observations.scores, pd.DataFrame)
        assert all_observations.contexts is None
        assert set(all_observations.configs.columns) == {"x", "y"}
        assert set(all_observations.scores.columns) == {"score"}
        assert len(all_observations.configs) == num_iters
        assert len(all_observations.scores) == num_iters
        assert len(all_observations) == num_iters

    # .surrogate_predict method not currently implemented if space adapter is employed
    if isinstance(llamatune_optimizer, BaseBayesianOptimizer):
        with pytest.raises(NotImplementedError):
            for obs in llamatune_best_observations:
                llamatune_optimizer.surrogate_predict(suggestion=obs.to_suggestion())


# Dynamically determine all of the optimizers we have implemented.
# Note: these must be sorted.
optimizer_subclasses: List[Type[BaseOptimizer]] = get_all_concrete_subclasses(
    BaseOptimizer,  # type: ignore[type-abstract]
    pkg_name="mlos_core",
)
assert optimizer_subclasses


@pytest.mark.parametrize(("optimizer_class"), optimizer_subclasses)
def test_optimizer_type_defs(optimizer_class: Type[BaseOptimizer]) -> None:
    """Test that all optimizer classes are listed in the OptimizerType enum."""
    optimizer_type_classes = {member.value for member in OptimizerType}
    assert optimizer_class in optimizer_type_classes


@pytest.mark.parametrize(
    ("optimizer_type", "kwargs"),
    [
        # Default optimizer
        (None, {}),
        # Enumerate all supported Optimizers
        *[(member, {}) for member in OptimizerType],
        # Optimizer with non-empty kwargs argument
    ],
)
def test_mixed_numerics_type_input_space_types(
    optimizer_type: Optional[OptimizerType],
    kwargs: Optional[dict],
) -> None:
    """Toy problem to test the optimizers with mixed numeric types to ensure that
    original dtypes are retained.
    """
    # pylint: disable=too-many-locals
    max_iterations = 10
    if kwargs is None:
        kwargs = {}

    def objective(point: pd.Series) -> pd.Series:
        # mix of hyperparameters, optimal is to select the highest possible
        ret: pd.Series = pd.Series({"score": point["x"] + point["y"]})
        return ret

    input_space = CS.ConfigurationSpace(seed=SEED)
    # add a mix of numeric datatypes
    input_space.add(CS.UniformIntegerHyperparameter(name="x", lower=0, upper=5))
    input_space.add(CS.UniformFloatHyperparameter(name="y", lower=0.0, upper=5.0))

    if optimizer_type is None:
        optimizer = OptimizerFactory.create(
            parameter_space=input_space,
            optimization_targets=["score"],
            optimizer_kwargs=kwargs,
        )
    else:
        optimizer = OptimizerFactory.create(
            parameter_space=input_space,
            optimization_targets=["score"],
            optimizer_type=optimizer_type,
            optimizer_kwargs=kwargs,
        )

    assert isinstance(optimizer, BaseOptimizer)

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_best_observations()

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_observations()

    for _ in range(max_iterations):
        suggestion = optimizer.suggest()
        assert isinstance(suggestion, Suggestion)
        assert isinstance(suggestion.config, pd.Series)
        assert set(suggestion.config.index) == {"x", "y"}
        # Check suggestion values are the expected dtype
        assert isinstance(suggestion.config["x"], int)
        assert isinstance(suggestion.config["y"], float)
        # Check that suggestion is in the space
        test_configuration = CS.Configuration(
            optimizer.parameter_space, suggestion.config.to_dict()
        )
        # Raises an error if outside of configuration space
        test_configuration.check_valid_configuration()
        # Test registering the suggested configuration with a score.
        observation = objective(suggestion.config)
        assert isinstance(observation, pd.Series)
        optimizer.register(observations=suggestion.complete(observation))

    best_observations = optimizer.get_best_observations()
    assert isinstance(best_observations.configs, pd.DataFrame)
    assert isinstance(best_observations.scores, pd.DataFrame)
    assert best_observations.contexts is None

    all_observations = optimizer.get_observations()
    assert isinstance(all_observations.configs, pd.DataFrame)
    assert isinstance(all_observations.scores, pd.DataFrame)
    assert all_observations.contexts is None
