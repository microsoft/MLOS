#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Basic initializer module for the mlos_core package.
"""

import ConfigSpace
import pandas as pd


def config_to_dataframe(config: ConfigSpace.Configuration) -> pd.DataFrame:
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
