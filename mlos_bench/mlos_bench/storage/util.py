#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Utility functions for the storage subsystem."""

from typing import Dict, Optional

import pandas

from mlos_bench.tunables.tunable import TunableValue, TunableValueTypeTuple
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
    if dataframe.columns.tolist() == ["metric", "value"]:
        dataframe = dataframe.copy()
        dataframe.rename(columns={"metric": "parameter"}, inplace=True)
    assert dataframe.columns.tolist() == ["parameter", "value"]
    data = {}
    for _, row in dataframe.astype("O").iterrows():
        if not isinstance(row["value"], TunableValueTypeTuple):
            raise TypeError(f"Invalid column type: {type(row['value'])} value: {row['value']}")
        assert isinstance(row["parameter"], str)
        if row["parameter"] in data:
            raise ValueError(f"Duplicate parameter '{row['parameter']}' in dataframe")
        data[row["parameter"]] = (
            try_parse_val(row["value"]) if isinstance(row["value"], str) else row["value"]
        )
    return data
