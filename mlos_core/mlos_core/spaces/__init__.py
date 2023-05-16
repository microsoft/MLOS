#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains some helper functions for converting config
"""

from typing import TYPE_CHECKING

import ConfigSpace
import numpy as np


if TYPE_CHECKING:
    import skopt.space
    import emukit.core


def configspace_to_skopt_space(config_space: ConfigSpace.ConfigurationSpace) -> "skopt.space.Space":
    """Converts a ConfigSpace.ConfigurationSpace to a list of skopt spaces.

    Parameters
    ----------
    config_space : ConfigSpace.ConfigurationSpace
        Input configuration space.

    Returns
    -------
    skopt.space.Space
    """
    import skopt.space  # pylint: disable=import-outside-toplevel

    def _one_parameter_convert(parameter: ConfigSpace.hyperparameters.Hyperparameter) -> "skopt.space.Dimension":
        if isinstance(parameter, ConfigSpace.UniformFloatHyperparameter):
            return skopt.space.Real(
                low=parameter.lower,
                high=parameter.upper,
                prior='uniform' if not parameter.log else 'log-uniform',
                name=parameter.name)
        elif isinstance(parameter, ConfigSpace.UniformIntegerHyperparameter):
            return skopt.space.Integer(
                low=parameter.lower,
                high=parameter.upper,
                prior='uniform' if not parameter.log else 'log-uniform',
                name=parameter.name)
        elif isinstance(parameter, ConfigSpace.CategoricalHyperparameter):
            return skopt.space.Categorical(categories=parameter.choices, prior=parameter.probabilities, name=parameter.name)
        raise ValueError(f"Type of parameter {parameter} ({type(parameter)}) not supported.")

    return skopt.space.Space([_one_parameter_convert(param) for param in config_space.get_hyperparameters()])


def configspace_to_emukit_space(config_space: ConfigSpace.ConfigurationSpace) -> "emukit.core.ParameterSpace":
    """Converts a ConfigSpace.ConfigurationSpace to emukit.core.ParameterSpace.

    Parameters
    ----------
    config_space : ConfigSpace.ConfigurationSpace
        Input configuration space.

    Returns
    -------
    emukit.core.ParameterSpace
    """
    import emukit.core  # pylint: disable=import-outside-toplevel

    def _one_parameter_convert(parameter: ConfigSpace.hyperparameters.Hyperparameter) -> "emukit.core.Parameter":
        log = getattr(parameter, 'log', False)
        if log and not isinstance(parameter, ConfigSpace.UniformIntegerHyperparameter):
            raise ValueError("Emukit doesn't support log parameters.")
        if isinstance(parameter, ConfigSpace.UniformFloatHyperparameter):
            return emukit.core.ContinuousParameter(name=parameter.name, min_value=parameter.lower, max_value=parameter.upper)
        elif isinstance(parameter, ConfigSpace.UniformIntegerHyperparameter):
            if log:
                return emukit.core.DiscreteParameter(
                    name=parameter.name,
                    domain=np.exp(np.arange(np.ceil(np.log(parameter.lower)), np.floor(np.log(parameter.upper + 1)))))
            return emukit.core.DiscreteParameter(name=parameter.name, domain=np.arange(parameter.lower, parameter.upper + 1))
        elif isinstance(parameter, ConfigSpace.CategoricalHyperparameter):
            if len(np.unique(parameter.probabilities)) > 1:
                raise ValueError("Emukit doesn't support categorical parameters with non-uniform probabilities.")
            encoding = emukit.core.OneHotEncoding(parameter.choices)
            return emukit.core.CategoricalParameter(name=parameter.name, encoding=encoding)
        raise ValueError(f"Type of parameter {parameter} ({type(parameter)}) not supported.")

    return emukit.core.ParameterSpace([_one_parameter_convert(param) for param in config_space.get_hyperparameters()])


def configspace_to_flaml_space(config_space: ConfigSpace.ConfigurationSpace) -> dict:
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
    # pylint: disable=import-outside-toplevel
    import flaml.tune
    import flaml.tune.sample

    flaml_numeric_type = {
        (ConfigSpace.UniformIntegerHyperparameter, False): flaml.tune.randint,
        (ConfigSpace.UniformIntegerHyperparameter, True): flaml.tune.lograndint,
        (ConfigSpace.UniformFloatHyperparameter, False): flaml.tune.uniform,
        (ConfigSpace.UniformFloatHyperparameter, True): flaml.tune.loguniform,
    }

    def _one_parameter_convert(parameter: ConfigSpace.hyperparameters.Hyperparameter) -> "flaml.tune.sample.Domain":
        if isinstance(parameter, (ConfigSpace.UniformFloatHyperparameter, ConfigSpace.UniformIntegerHyperparameter)):
            return flaml_numeric_type[(type(parameter), parameter.log)](parameter.lower, parameter.upper)
        elif isinstance(parameter, ConfigSpace.CategoricalHyperparameter):
            if len(np.unique(parameter.probabilities)) > 1:
                raise ValueError("FLAML doesn't support categorical parameters with non-uniform probabilities.")
            return flaml.tune.choice(parameter.choices)
        raise ValueError(f"Type of parameter {parameter} ({type(parameter)}) not supported.")

    return {param.name: _one_parameter_convert(param)
            for param in config_space.get_hyperparameters()}
