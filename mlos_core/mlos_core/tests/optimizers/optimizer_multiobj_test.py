#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Test multi-target optimization.
"""

import logging
import pytest

import pandas as pd
import numpy as np
import ConfigSpace as CS

from mlos_core.optimizers import OptimizerType, OptimizerFactory

from mlos_core.tests import SEED


_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


def test_multi_target_opt() -> None:
    """
    Toy multi-target optimization problem to test the optimizers with
    mixed numeric types to ensure that original dtypes are retained.
    """
    max_iterations = 10

    def objective(point: pd.DataFrame) -> pd.DataFrame:
        # mix of hyperparameters, optimal is to select the highest possible
        return pd.DataFrame({
            "score": point.x + point.y,
            "other_score": point.x ** 2 + point.y ** 2,
        })

    input_space = CS.ConfigurationSpace(seed=SEED)
    # add a mix of numeric datatypes
    input_space.add_hyperparameter(
        CS.UniformIntegerHyperparameter(name='x', lower=0, upper=5))
    input_space.add_hyperparameter(
        CS.UniformFloatHyperparameter(name='y', lower=0.0, upper=5.0))

    optimizer = OptimizerFactory.create(
        parameter_space=input_space,
        optimization_targets=['score', 'other_score'],
        optimizer_type=OptimizerType.SMAC,
        optimizer_kwargs={
            # Test with default config.
            'use_default_config': True,
            # 'n_random_init': 10,
        },
    )

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_best_observations()

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_observations()

    for _ in range(max_iterations):
        suggestion, context = optimizer.suggest()
        assert isinstance(suggestion, pd.DataFrame)
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
        assert set(observation.columns) == {'score', 'other_score'}
        optimizer.register(suggestion, observation, context)

    (best_config, best_score, best_context) = optimizer.get_best_observations()
    assert isinstance(best_config, pd.DataFrame)
    assert isinstance(best_score, pd.DataFrame)
    assert set(best_config.columns) == {'x', 'y'}
    assert set(best_score.columns) == {'score', 'other_score'}
    assert best_config.shape == (1, 2)
    assert best_score.shape == (1, 2)

    (all_configs, all_scores, all_contexts) = optimizer.get_observations()
    assert isinstance(all_configs, pd.DataFrame)
    assert isinstance(all_scores, pd.DataFrame)
    assert set(all_configs.columns) == {'x', 'y'}
    assert set(all_scores.columns) == {'score', 'other_score'}
    assert all_configs.shape == (max_iterations, 2)
    assert all_scores.shape == (max_iterations, 2)
