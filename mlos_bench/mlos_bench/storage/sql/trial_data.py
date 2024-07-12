#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""An interface to access the benchmark trial data stored in SQL DB."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import pandas
from sqlalchemy import Engine

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_trial_data import TrialData
from mlos_bench.storage.base_tunable_config_data import TunableConfigData
from mlos_bench.storage.sql.schema import DbSchema
from mlos_bench.storage.sql.tunable_config_data import TunableConfigSqlData
from mlos_bench.util import utcify_timestamp

if TYPE_CHECKING:
    from mlos_bench.storage.base_tunable_config_trial_group_data import (
        TunableConfigTrialGroupData,
    )


class TrialSqlData(TrialData):
    """An interface to access the trial data stored in the SQL DB."""

    def __init__(
        self,
        *,
        engine: Engine,
        schema: DbSchema,
        experiment_id: str,
        trial_id: int,
        config_id: int,
        ts_start: datetime,
        ts_end: Optional[datetime],
        status: Status,
    ):
        super().__init__(
            experiment_id=experiment_id,
            trial_id=trial_id,
            tunable_config_id=config_id,
            ts_start=ts_start,
            ts_end=ts_end,
            status=status,
        )
        self._engine = engine
        self._schema = schema

    @property
    def tunable_config(self) -> TunableConfigData:
        """
        Retrieve the trial's tunable configuration from the storage.

        Note: this corresponds to the Trial object's "tunables" property.
        """
        return TunableConfigSqlData(
            engine=self._engine,
            schema=self._schema,
            tunable_config_id=self._tunable_config_id,
        )

    @property
    def tunable_config_trial_group(self) -> "TunableConfigTrialGroupData":
        """Retrieve the trial's tunable config group configuration data from the
        storage.
        """
        # pylint: disable=import-outside-toplevel
        from mlos_bench.storage.sql.tunable_config_trial_group_data import (
            TunableConfigTrialGroupSqlData,
        )

        return TunableConfigTrialGroupSqlData(
            engine=self._engine,
            schema=self._schema,
            experiment_id=self._experiment_id,
            tunable_config_id=self._tunable_config_id,
        )

    @property
    def results_df(self) -> pandas.DataFrame:
        """Retrieve the trials' results from the storage."""
        with self._engine.connect() as conn:
            cur_results = conn.execute(
                self._schema.trial_result.select()
                .where(
                    self._schema.trial_result.c.exp_id == self._experiment_id,
                    self._schema.trial_result.c.trial_id == self._trial_id,
                )
                .order_by(
                    self._schema.trial_result.c.metric_id,
                )
            )
            return pandas.DataFrame(
                [(row.metric_id, row.metric_value) for row in cur_results.fetchall()],
                columns=["metric", "value"],
            )

    @property
    def telemetry_df(self) -> pandas.DataFrame:
        """Retrieve the trials' telemetry from the storage."""
        with self._engine.connect() as conn:
            cur_telemetry = conn.execute(
                self._schema.trial_telemetry.select()
                .where(
                    self._schema.trial_telemetry.c.exp_id == self._experiment_id,
                    self._schema.trial_telemetry.c.trial_id == self._trial_id,
                )
                .order_by(
                    self._schema.trial_telemetry.c.ts,
                    self._schema.trial_telemetry.c.metric_id,
                )
            )
            # Not all storage backends store the original zone info.
            # We try to ensure data is entered in UTC and augment it on return again here.
            return pandas.DataFrame(
                [
                    (utcify_timestamp(row.ts, origin="utc"), row.metric_id, row.metric_value)
                    for row in cur_telemetry.fetchall()
                ],
                columns=["ts", "metric", "value"],
            )

    @property
    def metadata_df(self) -> pandas.DataFrame:
        """
        Retrieve the trials' metadata params.

        Note: this corresponds to the Trial object's "config" property.
        """
        with self._engine.connect() as conn:
            cur_params = conn.execute(
                self._schema.trial_param.select()
                .where(
                    self._schema.trial_param.c.exp_id == self._experiment_id,
                    self._schema.trial_param.c.trial_id == self._trial_id,
                )
                .order_by(
                    self._schema.trial_param.c.param_id,
                )
            )
            return pandas.DataFrame(
                [(row.param_id, row.param_value) for row in cur_params.fetchall()],
                columns=["parameter", "value"],
            )
