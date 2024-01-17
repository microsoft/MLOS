#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Internal helper functions for mlos_core package.
"""

from typing import Union

from ConfigSpace import Configuration, ConfigurationSpace
import pandas as pd


def config_to_dataframe(config: Configuration) -> pd.DataFrame:
    """Converts a ConfigSpace config to a DataFrame

    Parameters
    ----------
    config : ConfigSpace.Configuration
        The config to convert.

    Returns
    -------
    pd.DataFrame
        A DataFrame with a single row, containing the config's parameters.
    """
    return pd.DataFrame([dict(config)])


def normalize_config(config_space: ConfigurationSpace, config: Union[Configuration, dict]) -> Configuration:
    """
    Convert a dictionary to a valid ConfigSpace configuration.

    Some optimizers and adapters ignore ConfigSpace conditionals when proposing new
    configurations. We have to manually remove inactive hyperparameters such suggestions.

    Parameters
    ----------
    config_space : ConfigurationSpace
        The parameter space to use.
    config : dict
        The configuration to convert.

    Returns
    -------
    cs_config: Configuration
        A valid ConfigSpace configuration with inactive parameters removed.
    """
    cs_config = Configuration(config_space, values=config, allow_inactive_with_values=True)
    return Configuration(
        config_space, values={
            key: cs_config[key]
            for key in config_space.get_active_hyperparameters(cs_config)
        }
    )
