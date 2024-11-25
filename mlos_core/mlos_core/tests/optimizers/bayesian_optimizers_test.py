#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for Bayesian Optimizers."""

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
        *[(member.value, {}) for member in OptimizerType],
    ],
)
def test_context_not_implemented_warning(
    configuration_space: CS.ConfigurationSpace,
    optimizer_class: Type[BaseOptimizer],
    kwargs: Optional[dict],
) -> None:
    """Make sure we raise warnings for the functionality that has not been implemented
    yet.
    """
    if kwargs is None:
        kwargs = {}
    optimizer = optimizer_class(
        parameter_space=configuration_space,
        optimization_targets=["score"],
        **kwargs,
    )
    suggestion = optimizer.suggest()
    scores = pd.Series({"score": [1]})
    context = pd.Series([["something"]])

    suggestion._context = context  # pylint: disable=protected-access
    with pytest.raises(UserWarning):
        optimizer.register(observations=suggestion.complete(scores))

    with pytest.raises(UserWarning):
        optimizer.suggest(context=context)

    if isinstance(optimizer, BaseBayesianOptimizer):
        with pytest.raises(UserWarning):
            optimizer.surrogate_predict(suggestion=suggestion)
