#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Test fixtures for mlos_bench optimizers."""

import ConfigSpace as CS
import pytest


@pytest.fixture
def configuration_space() -> CS.ConfigurationSpace:
    """Test fixture to produce a config space with all types of hyperparameters."""
    # Start defining a ConfigurationSpace for the Optimizer to search.
    space = CS.ConfigurationSpace(seed=1234)
    # Add a continuous input dimension between 0 and 1.
    space.add_hyperparameter(CS.UniformFloatHyperparameter(name="x", lower=0, upper=1))
    # Add a categorical hyperparameter with 3 possible values.
    space.add_hyperparameter(CS.CategoricalHyperparameter(name="y", choices=["a", "b", "c"]))
    # Add a discrete input dimension between 0 and 10.
    space.add_hyperparameter(CS.UniformIntegerHyperparameter(name="z", lower=0, upper=10))
    return space
