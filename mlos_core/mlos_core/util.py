#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Internal helper functions for mlos_core package."""


import pandas as pd
from ConfigSpace import Configuration, ConfigurationSpace


def compare_optional_series(left: pd.Series | None, right: pd.Series | None) -> bool:
    """
    Compare Series that may also be None.

    Parameters
    ----------
    left : pandas.Series | None
        The left Series to compare
    right : pandas.Series | None
        The right Series to compare

    Returns
    -------
    bool
        Compare the equality of two pd.Series | None objects
    """
    if isinstance(left, pd.Series) and isinstance(right, pd.Series):
        return left.equals(right)
    return left is None and right is None


def compare_optional_dataframe(
    left: pd.DataFrame | None,
    right: pd.DataFrame | None,
) -> bool:
    """
    Compare DataFrames that may also be None.

    Parameters
    ----------
    left : pandas.DataFrame | None
        The left DataFrame to compare
    right : pandas.DataFrame | None
        The right DataFrame to compare

    Returns
    -------
    bool
        Compare the equality of two pd.DataFrame | None objects
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
    pandas.Series
        A Series, containing the config's parameters.
    """
    series: pd.Series = pd.Series(dict(config))  # needed for type hinting
    return series


def drop_nulls(d: dict) -> dict:
    """
    Remove all key-value pairs where the value is None.

    Parameters
    ----------
    d : dict
        The dictionary to clean.

    Returns
    -------
    dict
        The cleaned dictionary.
    """
    return {k: v for k, v in d.items() if v is not None}


def normalize_config(
    config_space: ConfigurationSpace,
    config: Configuration | dict,
) -> Configuration:
    """
    Convert a dictionary to a valid ConfigSpace configuration.

    Some optimizers and adapters ignore ConfigSpace conditionals when proposing new
    configurations. We have to manually remove inactive hyperparameters such suggestions.

    Parameters
    ----------
    config_space : ConfigSpace.ConfigurationSpace
        The parameter space to use.
    config : dict
        The configuration to convert.

    Returns
    -------
    cs_config: ConfigSpace.Configuration
        A valid ConfigSpace configuration with inactive parameters removed.
    """
    cs_config = Configuration(config_space, values=config, allow_inactive_with_values=True)
    return Configuration(
        config_space,
        values={key: cs_config[key] for key in config_space.get_active_hyperparameters(cs_config)},
    )
