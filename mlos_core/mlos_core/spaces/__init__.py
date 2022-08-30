"""
Contains some helper functions for converting config
"""

import ConfigSpace
import numpy as np


def configspace_to_skopt_space(config_space: ConfigSpace.ConfigurationSpace):
    """Converts a ConfigSpace.ConfigurationSpace to a list of skopt spaces.

    Parameters
    ----------
    config_space : ConfigSpace.ConfigurationSpace
        Input configuration space.

    Returns
    -------
    list of skopt.space.Space
    """
    import skopt.space  # pylint: disable=import-outside-toplevel

    def _one_parameter_convert(parameter):
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


def configspace_to_emukit_space(config_space: ConfigSpace.ConfigurationSpace):
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

    def _one_parameter_convert(parameter):
        log = getattr(parameter, 'log', False)
        if log and not isinstance(parameter, ConfigSpace.UniformIntegerHyperparameter):
            raise ValueError("Emukit doesn't support log parameters.")
        if isinstance(parameter, ConfigSpace.UniformFloatHyperparameter):
            return emukit.core.ContinuousParameter(name=parameter.name, min_value=parameter.lower, max_value=parameter.upper)
        elif isinstance(parameter, ConfigSpace.UniformIntegerHyperparameter):
            if log:
                return emukit.core.DiscreteParameter(
                    name=parameter.name,
                    domain=np.exp(np.arange(np.ceil(np.log(parameter.lower)), np.floor(np.log(parameter.upper+1)))))
            return emukit.core.DiscreteParameter(name=parameter.name, domain=np.arange(parameter.lower, parameter.upper + 1))
        elif isinstance(parameter, ConfigSpace.CategoricalHyperparameter):
            if len(np.unique(parameter.probabilities)) > 1:
                raise ValueError("Emukit doesn't support categorical parameters with non-uniform probabilities.")
            encoding = emukit.core.OneHotEncoding(parameter.choices)
            return emukit.core.CategoricalParameter(name=parameter.name, encoding=encoding)
        raise ValueError(f"Type of parameter {parameter} ({type(parameter)}) not supported.")

    return emukit.core.ParameterSpace([_one_parameter_convert(param) for param in config_space.get_hyperparameters()])
