#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
An interface to access the benchmark data stored in SQL DB.
"""

from typing import Dict

from sqlalchemy import Engine

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.storage.sql.schema import DbSchema
from mlos_bench.storage.base_trial_data import TrialData
from mlos_bench.storage.sql.trial_data import TrialSqlData


class ExperimentSqlData(ExperimentData):
    """
    Base interface for accessing the stored benchmark data.
    """

    def __init__(self, engine: Engine, schema: DbSchema, exp_id: str):
        super().__init__(exp_id)
        self._engine = engine
        self._schema = schema

    @property
    def trials(self) -> Dict[int, TrialData]:
        with self._engine.connect() as conn:
            cur_trials = conn.execute(
                self._schema.trial.select().where(
                    self._schema.trial.c.exp_id == self._exp_id,
                ).order_by(
                    self._schema.trial.c.exp_id.asc(),
                    self._schema.trial.c.trial_id.asc(),
                )
            )
            return {
                trial.trial_id: TriaSqlData(
                    self._engine, self._schema, self._exp_id, trial.trial_id, trial.config_id,
                    trial.ts_start, trial.ts_end, Status[trial.status])
                for trial in cur_trials.fetchall()
            }
