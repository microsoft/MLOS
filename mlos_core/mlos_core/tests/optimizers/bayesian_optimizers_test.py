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


@pytest.mark.parametrize(
    ("optimizer_class", "kwargs"),
    [
        *[(member.value, {}) for member in OptimizerType],
    ],
)
def test_context_not_implemented_error(
    configuration_space: CS.ConfigurationSpace,
    optimizer_class: Type[BaseOptimizer],
    kwargs: Optional[dict],
) -> None:
    """
    Make sure we raise exceptions for the functionality that has not been implemented yet.
    """
    if kwargs is None:
        kwargs = {}
    optimizer = optimizer_class(parameter_space=configuration_space, **kwargs)
    suggestion = optimizer.suggest()
    scores = pd.DataFrame({"score": [1]})
    # test context not implemented errors
    with pytest.raises(NotImplementedError):
        optimizer.register(
            suggestion, scores["score"], context=pd.DataFrame([["something"]])
        )

    with pytest.raises(NotImplementedError):
        optimizer.suggest(context=pd.DataFrame([["something"]]))

    if isinstance(optimizer, BaseBayesianOptimizer):
        with pytest.raises(NotImplementedError):
            optimizer.surrogate_predict(
                suggestion, context=pd.DataFrame([["something"]])
            )
