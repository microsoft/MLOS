#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Utility functions for the storage subsystem.
"""

from datetime import datetime, UTC
from typing import Dict, Literal, Optional

import pandas

from mlos_bench.tunables.tunable import TunableValue, TunableValueTypeTuple
from mlos_bench.util import try_parse_val


def utcify_timestamp(timestamp: datetime, *, origin: Literal["utc", "local"]) -> datetime:
    """
    Augment a timestamp with zoneinfo if missing and convert it to UTC.

    Parameters
    ----------
    timestamp : datetime
        A timestamp to convert to UTC.
        Note: The original datetime may or may not have tzinfo associated with it.

    origin : Literal["utc", "local"]
        Whether the source timestamp is considered to be in UTC or local time.
        In the case of loading data from storage, where we intentionally convert all
        timestamps to UTC, this can help us retrieve the original timezone when the
        storage backend doesn't explicitly store it.
    Returns
    -------
    datetime
        A datetime with zoneinfo in UTC.
    """
    if timestamp.tzinfo is not None or origin == "local":
        # A timestamp with no zoneinfo is interpretted as "local" time
        # (e.g., according to the TZ environment variable).
        # That could be UTC or some other timezone, but either way we convert it to
        # be explicitly UTC with zone info.
        return timestamp.astimezone(UTC)
    elif origin == "utc":
        # If the timestamp is already in UTC, we just add the zoneinfo without conversion.
        # Converting with astimezone() when the local time is *not* UTC would cause
        # a timestamp conversion which we don't want.
        return timestamp.replace(tzinfo=UTC)
    else:
        raise ValueError(f"Invalid origin: {origin}")


def utcify_nullable_timestamp(timestamp: Optional[datetime], *, origin: Literal["utc", "local"]) -> Optional[datetime]:
    """
    A nullable version of utcify_timestamp.
    """
    return utcify_timestamp(timestamp, origin=origin) if timestamp is not None else None


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
    for _, row in dataframe.astype('O').iterrows():
        if not isinstance(row['value'], TunableValueTypeTuple):
            raise TypeError(f"Invalid column type: {type(row['value'])} value: {row['value']}")
        assert isinstance(row['parameter'], str)
        if row['parameter'] in data:
            raise ValueError(f"Duplicate parameter '{row['parameter']}' in dataframe")
        data[row['parameter']] = try_parse_val(row['value']) if isinstance(row['value'], str) else row['value']
    return data
