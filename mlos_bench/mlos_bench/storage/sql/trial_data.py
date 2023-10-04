#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base interface for accessing the stored benchmark data.
"""
from datetime import datetime
from typing import Optional

import pandas
from sqlalchemy import Engine

from mlos_bench.storage.base_trial_data import TrialData
from mlos_bench.environments.status import Status
from mlos_bench.storage.sql.schema import DbSchema


class TrialSqlData(TrialData):
    """
    An interface to access the trial data stored in the SQL DB.
    """

    def __init__(self, *,
                 engine: Engine,
                 schema: DbSchema,
                 exp_id: str,
                 trial_id: int,
                 config_id: int,
                 ts_start: datetime,
                 ts_end: Optional[datetime],
                 status: Status):
        super().__init__(
            exp_id=exp_id,
            trial_id=trial_id,
            config_id=config_id,
            ts_start=ts_start,
            ts_end=ts_end,
            status=status,
        )
        self._engine = engine
        self._schema = schema

    @property
    def config(self) -> pandas.DataFrame:
        """
        Retrieve the trials' configuration from the storage.
        """
        return pandas.DataFrame()

    @property
    def results(self) -> pandas.DataFrame:
        """
        Retrieve the trials' results from the storage.
        """
        return pandas.DataFrame()

    @property
    def telemetry(self) -> pandas.DataFrame:
        """
        Retrieve the trials' telemetry from the storage.
        """
        return pandas.DataFrame()

    @property
    def metadata(self) -> pandas.DataFrame:
        """
        Retrieve the trials' metadata.
        """
        return pandas.DataFrame()
