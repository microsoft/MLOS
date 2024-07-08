#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for Optimizers using Metadata.
"""

from typing import Callable

import logging
import pytest

import pandas as pd
import ConfigSpace as CS

from smac import MultiFidelityFacade as MFFacade
from smac.intensifier.successive_halving import SuccessiveHalving

from mlos_core.optimizers import (
    OptimizerType, OptimizerFactory, BaseOptimizer)
from mlos_core.tests import SEED

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


def smac_verify_best(metadata: pd.DataFrame) -> bool:
    """
    Function to verify if the metadata used by SMAC is in a legal state

    Parameters
    ----------
    metadata : pd.DataFrame
        metadata returned by SMAC

    Returns
    -------
    bool
        if the metadata that is returned is valid
    """
    max_budget = metadata["budget"].max()
    if isinstance(max_budget, float):
        return max_budget == 9
    return False


@pytest.mark.parametrize(('optimizer_type', 'verify', 'kwargs'), [
    # Enumerate all supported Optimizers
    *[(member, verify, {"seed": SEED, "facade": MFFacade, "intensifier": SuccessiveHalving, "min_budget": 1, "max_budget": 9})
      for member, verify in [(OptimizerType.SMAC, smac_verify_best)]],
])
def test_optimizer_metadata(optimizer_type: OptimizerType, verify: Callable[[pd.DataFrame], bool], kwargs: dict) -> None:
    """
    Toy problem to test if metadata is properly being handled for each supporting optimizer
    """
    max_iterations = 100

    def objective(point: pd.DataFrame) -> pd.DataFrame:
        # mix of hyperparameters, optimal is to select the highest possible
        return pd.DataFrame({"score": point["x"] + point["y"]})

    input_space = CS.ConfigurationSpace(seed=SEED)
    # add a mix of numeric datatypes
    input_space.add_hyperparameter(CS.UniformIntegerHyperparameter(name='x', lower=0, upper=5))
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='y', lower=0.0, upper=5.0))

    optimizer: BaseOptimizer = OptimizerFactory.create(
        parameter_space=input_space,
        optimization_targets=['score'],
        optimizer_type=optimizer_type,
        optimizer_kwargs=kwargs,
    )

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_best_observations()

    with pytest.raises(ValueError, match="No observations"):
        optimizer.get_observations()

    for _ in range(max_iterations):
        config, metadata = optimizer.suggest()
        assert isinstance(metadata, pd.DataFrame)

        optimizer.register(configs=config, scores=objective(config), metadata=metadata)

    (all_configs, all_scores, all_contexts, all_metadata) = optimizer.get_observations()
    assert isinstance(all_configs, pd.DataFrame)
    assert isinstance(all_scores, pd.DataFrame)
    assert all_contexts is None
    assert isinstance(all_metadata, pd.DataFrame)
    assert smac_verify_best(all_metadata)

    (best_configs, best_scores, best_contexts, best_metadata) = optimizer.get_best_observations()
    assert isinstance(best_configs, pd.DataFrame)
    assert isinstance(best_scores, pd.DataFrame)
    assert best_contexts is None
    assert isinstance(best_metadata, pd.DataFrame)
    assert verifier(best_metadata)
