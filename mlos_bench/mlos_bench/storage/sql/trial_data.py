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
    def tunable_config(self) -> pandas.DataFrame:
        """
        Retrieve the trials' tunable configuration from the storage.

        Note: this corresponds to the Trial object's "tunables" property.
        """
        with self._engine.connect() as conn:
            cur_config = conn.execute(
                self._schema.config_param.select().where(
                    self._schema.config_param.c.config_id == self._config_id
                ).order_by(
                    self._schema.config_param.c.param_id,
                )
            )
            return pandas.DataFrame(
                [(row.param_id, row.param_value) for row in cur_config.fetchall()],
                columns=['parameter', 'value'])

    @property
    def results(self) -> pandas.DataFrame:
        """
        Retrieve the trials' results from the storage.
        """
        with self._engine.connect() as conn:
            cur_results = conn.execute(
                self._schema.trial_result.select().where(
                    self._schema.trial_result.c.exp_id == self._exp_id,
                    self._schema.trial_result.c.trial_id == self._trial_id
                ).order_by(
                    self._schema.trial_result.c.metric_id,
                )
            )
            return pandas.DataFrame(
                [(row.metric_id, row.metric_value) for row in cur_results.fetchall()],
                columns=['metric', 'value'])

    @property
    def telemetry(self) -> pandas.DataFrame:
        """
        Retrieve the trials' telemetry from the storage.
        """
        with self._engine.connect() as conn:
            cur_telemetry = conn.execute(
                self._schema.trial_telemetry.select().where(
                    self._schema.trial_telemetry.c.exp_id == self._exp_id,
                    self._schema.trial_telemetry.c.trial_id == self._trial_id
                ).order_by(
                    self._schema.trial_telemetry.c.ts,
                    self._schema.trial_telemetry.c.metric_id,
                )
            )
            return pandas.DataFrame(
                [(row.ts, row.metric_id, row.metric_value) for row in cur_telemetry.fetchall()],
                columns=['ts', 'metric', 'value'])

    @property
    def metadata(self) -> pandas.DataFrame:
        """
        Retrieve the trials' metadata params.

        Note: this corresponds to the Trial object's "config" property.
        """
        with self._engine.connect() as conn:
            cur_params = conn.execute(
                self._schema.trial_param.select().where(
                    self._schema.trial_param.c.exp_id == self._exp_id,
                    self._schema.trial_param.c.trial_id == self._trial_id
                ).order_by(
                    self._schema.trial_param.c.param_id,
                )
            )
            return pandas.DataFrame(
                [(row.param_id, row.param_value) for row in cur_params.fetchall()],
                columns=['parameter', 'value'])
