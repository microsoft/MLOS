#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for Bayesian Optimizers.
"""

from typing import Optional, Type

import pytest

import pandas as pd
import ConfigSpace as CS

from mlos_core.optimizers import BaseOptimizer, OptimizerType
from mlos_core.optimizers.bayesian_optimizers import BaseBayesianOptimizer


@pytest.mark.filterwarnings("error:Not Implemented")
@pytest.mark.parametrize(('optimizer_class', 'kwargs'), [
    *[(member.value, {}) for member in OptimizerType],
])
def test_context_not_implemented_warning(configuration_space: CS.ConfigurationSpace,
                                         optimizer_class: Type[BaseOptimizer],
                                         kwargs: Optional[dict]) -> None:
    """
    Make sure we raise warnings for the functionality that has not been implemented yet.
    """
    if kwargs is None:
        kwargs = {}
    optimizer = optimizer_class(
        parameter_space=configuration_space,
        optimization_targets=['score'],
        **kwargs
    )
    suggestion, _metadata = optimizer.suggest()
    scores = pd.DataFrame({'score': [1]})
    context = pd.DataFrame([["something"]])

    with pytest.raises(UserWarning):
        optimizer.register(configs=suggestion, scores=scores, context=context)

    with pytest.raises(UserWarning):
        optimizer.suggest(context=context)

    if isinstance(optimizer, BaseBayesianOptimizer):
        with pytest.raises(UserWarning):
            optimizer.surrogate_predict(configs=suggestion, context=context)
