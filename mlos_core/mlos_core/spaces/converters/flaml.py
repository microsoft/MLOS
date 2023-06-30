#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains space converters for FLAML.
"""

from typing import Dict, TypeAlias

import ConfigSpace
import numpy as np

import flaml.tune
import flaml.tune.sample


FlamlDomain: TypeAlias = flaml.tune.sample.Domain
FlamlSpace: TypeAlias = Dict[str, flaml.tune.sample.Domain]


def configspace_to_flaml_space(config_space: ConfigSpace.ConfigurationSpace) -> Dict[str, FlamlDomain]:
    """Converts a ConfigSpace.ConfigurationSpace to dict.

    Parameters
    ----------
    config_space : ConfigSpace.ConfigurationSpace
        Input configuration space.

    Returns
    -------
    flaml_space : dict
        A dictionary of flaml.tune.sample.Domain objects keyed by parameter name.
    """
    flaml_numeric_type = {
        (ConfigSpace.UniformIntegerHyperparameter, False): flaml.tune.randint,
        (ConfigSpace.UniformIntegerHyperparameter, True): flaml.tune.lograndint,
        (ConfigSpace.UniformFloatHyperparameter, False): flaml.tune.uniform,
        (ConfigSpace.UniformFloatHyperparameter, True): flaml.tune.loguniform,
    }

    def _one_parameter_convert(parameter: ConfigSpace.hyperparameters.Hyperparameter) -> FlamlDomain:
        if isinstance(parameter, (ConfigSpace.UniformFloatHyperparameter, ConfigSpace.UniformIntegerHyperparameter)):
            return flaml_numeric_type[(type(parameter), parameter.log)](parameter.lower, parameter.upper)
        elif isinstance(parameter, ConfigSpace.CategoricalHyperparameter):
            if len(np.unique(parameter.probabilities)) > 1:
                raise ValueError("FLAML doesn't support categorical parameters with non-uniform probabilities.")
            return flaml.tune.choice(parameter.choices)     # TODO: set order?
        raise ValueError(f"Type of parameter {parameter} ({type(parameter)}) not supported.")

    return {param.name: _one_parameter_convert(param) for param in config_space.values()}
