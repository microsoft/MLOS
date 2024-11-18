#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Internal helper functions for mlos_core package."""

from typing import Optional, Union

import pandas as pd
from ConfigSpace import Configuration, ConfigurationSpace


def compare_optional_series(left: Optional[pd.Series], right: Optional[pd.Series]) -> bool:
    """
    Compare Series that may also be None.

    Parameters
    ----------
    left : Optional[pd.Series]
        The left Series to compare
    right : Optional[pd.Series]
        The right Series to compare

    Returns
    -------
    bool
        Compare the equality of two Optional[pd.Series] objects
    """
    if isinstance(left, pd.Series) and isinstance(right, pd.Series):
        return left.equals(right)
    return left is None and right is None


def compare_optional_dataframe(
    left: Optional[pd.DataFrame],
    right: Optional[pd.DataFrame],
) -> bool:
    """
    Compare DataFrames that may also be None.

    Parameters
    ----------
    left : Optional[pd.DataFrame]
        The left DataFrame to compare
    right : Optional[pd.DataFrame]
        The right DataFrame to compare

    Returns
    -------
    bool
        Compare the equality of two Optional[pd.DataFrame] objects
    """
    if isinstance(left, pd.DataFrame) and isinstance(right, pd.DataFrame):
        return left.equals(right)
    return left is None and right is None


def config_to_series(config: Configuration) -> pd.Series:
    """
    Converts a ConfigSpace config to a Series.

    Parameters
    ----------
    config : ConfigSpace.Configuration
        The config to convert.

    Returns
    -------
    pd.Series
        A Series, containing the config's parameters.
    """
    return pd.Series(dict(config))


def normalize_config(
    config_space: ConfigurationSpace,
    config: Union[Configuration, dict],
) -> Configuration:
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
        config_space,
        values={key: cs_config[key] for key in config_space.get_active_hyperparameters(cs_config)},
    )
