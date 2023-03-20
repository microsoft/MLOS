#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for Bayesian Optimizers.
"""

from typing import Type

import pytest

import pandas as pd
import ConfigSpace as CS

from mlos_core.optimizers import BaseOptimizer, EmukitOptimizer, SkoptOptimizer


@pytest.mark.parametrize(('optimizer_class', 'kwargs'), [
    (EmukitOptimizer, {}),
    (SkoptOptimizer, {'base_estimator': 'gp'}),
])
def test_context_not_implemented_error(configuration_space: CS.ConfigurationSpace,
                                       optimizer_class: Type[BaseOptimizer], kwargs):
    """
    Make sure we raise exceptions for the functionality that has not been implemented yet.
    """
    optimizer = optimizer_class(configuration_space, **kwargs)
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
