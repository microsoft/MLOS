#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Utility functions for the storage subsystem.
"""

from typing import Dict, Optional

import pandas

from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.util import try_parse_val


def kv_df_to_dict(dataframe: pandas.DataFrame) -> Dict[str, Optional[TunableValue]]:
    """
    Utility function to convert certain flat key-value dataframe formats used by the
    mlos_bench.storage modules to a dict.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        A dataframe with exactly two columns, 'parameter' (or 'metric') and 'value', where
        'parameter' is a string and 'value' is some TunableValue or None.
    """
    if dataframe.columns.tolist() == ['metric', 'value']:
        dataframe = dataframe.copy()
        dataframe.rename(columns={'metric': 'parameter'}, inplace=True)
    assert dataframe.columns.tolist() == ['parameter', 'value']
    data = {}
    for _, row in dataframe.iterrows():
        assert isinstance(row['parameter'], str)
        assert row['value'] is None or isinstance(row['value'], (str, int, float))
        if row['parameter'] in data:
            raise ValueError(f"Duplicate parameter '{row['parameter']}' in dataframe")
        data[row['parameter']] = try_parse_val(row['value']) if isinstance(row['value'], str) else row['value']
    return data
