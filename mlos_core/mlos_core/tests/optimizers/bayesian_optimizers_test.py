#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for Bayesian Optimizers.
"""

from typing import Optional, Type

import ConfigSpace as CS
import pandas as pd
import pytest
from mlos_core.optimizers import BaseOptimizer, OptimizerType
from mlos_core.optimizers.bayesian_optimizers import BaseBayesianOptimizer


@pytest.mark.filterwarnings("error:Not Implemented")
@pytest.mark.parametrize(
    ("optimizer_class", "kwargs"),
    [
        *[(member.value, {}) for member in OptimizerType if not member == OptimizerType.SMAC],
    ],
)
def test_context_not_implemented_warning(
    configuration_space: CS.ConfigurationSpace,
    optimizer_class: Type[BaseOptimizer],
    kwargs: Optional[dict],
) -> None:
    """
    Make sure we raise warnings for the functionality that has not been implemented yet.
    """
    if kwargs is None:
        kwargs = {}
    optimizer = optimizer_class(parameter_space=configuration_space, **kwargs)
    suggestion, _ = optimizer.suggest()
    scores = pd.DataFrame({"score": [1]})
    context = pd.DataFrame([["something"]])
    # test context not implemented errors
    with pytest.raises(UserWarning):
        optimizer.register(suggestion, scores["score"], context=context)

    with pytest.raises(UserWarning):
        optimizer.suggest(context=context)

    if isinstance(optimizer, BaseBayesianOptimizer):
        with pytest.raises(UserWarning):
            optimizer.surrogate_predict(suggestion, context=context)
