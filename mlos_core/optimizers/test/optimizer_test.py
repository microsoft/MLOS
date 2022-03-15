"""
Tests for Bayesian Optimizers.
"""

from typing import Type

import pytest

import ConfigSpace as CS

from mlos_core.optimizers import BaseOptimizer, EmukitOptimizer, SkoptOptimizer, RandomOptimizer

@pytest.mark.parametrize(('optimizer_class', 'kwargs'), [
    (EmukitOptimizer, {}),
    (SkoptOptimizer, {'base_estimator': 'gp'}),
    (RandomOptimizer, {})
])
def test_create_optimizer_and_suggest(optimizer_class: Type[BaseOptimizer], kwargs):
    """
    Helper method for testing optimizers.
    """
    # Start defining a ConfigurationSpace for the Optimizer to search.
    input_space = CS.ConfigurationSpace(seed=1234)

    # Add a single continuous input dimension between 0 and 1.
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='x', lower=0, upper=1))

    optimizer = optimizer_class(input_space, **kwargs)
    assert optimizer is not None

    assert optimizer.parameter_space is not None

    suggestion = optimizer.suggest()
    assert suggestion is not None
