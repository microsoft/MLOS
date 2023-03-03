"""
Tests for Bayesian Optimizers.
"""

# pylint: disable=missing-function-docstring

from typing import Type

import pytest

import pandas as pd
import ConfigSpace as CS

from mlos_core.optimizers import BaseOptimizer, EmukitOptimizer, SkoptOptimizer


@pytest.mark.parametrize(('optimizer_class', 'kwargs'), [
    (EmukitOptimizer, {}),
    (SkoptOptimizer, {'base_estimator': 'gp'}),
])
def test_context_not_implemented_error(optimizer_class: Type[BaseOptimizer], kwargs):
    input_space = CS.ConfigurationSpace(seed=1234)
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='x', lower=0, upper=1))
    optimizer = optimizer_class(input_space, **kwargs)
    suggestion = optimizer.suggest()
    score = pd.DataFrame({'score': [1]})
    # test context not implemented errors
    with pytest.raises(NotImplementedError):
        optimizer.register(suggestion, score, context="something")

    with pytest.raises(NotImplementedError):
        optimizer.suggest(context="something")

    with pytest.raises(NotImplementedError):
        optimizer.surrogate_predict(suggestion, context="something")

    # acquisition function not implemented
    with pytest.raises(NotImplementedError):
        optimizer.acquisition_function(suggestion)
