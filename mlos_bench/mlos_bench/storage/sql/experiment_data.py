#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
An interface to access the benchmark data stored in SQL DB.
"""
from typing import Dict

import pandas
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

    def __init__(self, *, engine: Engine, schema: DbSchema, exp_id: str,
                 description: str, root_env_config: str, git_repo: str, git_commit: str):
        super().__init__(
            exp_id=exp_id,
            description=description,
            root_env_config=root_env_config,
            git_repo=git_repo,
            git_commit=git_commit,
        )
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
                trial.trial_id: TrialSqlData(
                    engine=self._engine,
                    schema=self._schema,
                    exp_id=self._exp_id,
                    trial_id=trial.trial_id,
                    config_id=trial.config_id,
                    ts_start=trial.ts_start,
                    ts_end=trial.ts_end,
                    status=Status[trial.status],
                )
                for trial in cur_trials.fetchall()
            }

    @property
    def results(self) -> pandas.DataFrame:

        with self._engine.connect() as conn:

            cur_trials = conn.execute(
                self._schema.trial.select().where(
                    self._schema.trial.c.exp_id == self._exp_id,
                ).order_by(
                    self._schema.trial.c.exp_id.asc(),
                    self._schema.trial.c.trial_id.asc(),
                )
            )
            trials_df = pandas.DataFrame(
                [(row.trial_id, row.ts_start, row.ts_end, row.config_id, row.status)
                 for row in cur_trials.fetchall()],
                columns=['trial_id', 'ts_start', 'ts_end', 'config_id', 'status'])

            cur_configs = conn.execute(
                self._schema.trial.select().with_only_columns(
                    self._schema.trial.c.trial_id,
                    self._schema.trial.c.config_id,
                    self._schema.config_param.c.param_id,
                    self._schema.config_param.c.param_value,
                ).where(
                    self._schema.trial.c.exp_id == self._exp_id,
                ).join(
                    self._schema.config_param,
                    self._schema.config_param.c.config_id == self._schema.trial.c.config_id,
                    isouter=True
                ).order_by(
                    self._schema.trial.c.trial_id,
                )
            )
            configs_df = pandas.DataFrame(
                [(row.trial_id, row.config_id, "config." + row.param_id, row.param_value)
                 for row in cur_configs.fetchall()],
                columns=['trial_id', 'config_id', 'param', 'value']
            ).pivot(
                index=["trial_id", "config_id"], columns="param", values="value",
            ).apply(pandas.to_numeric, errors='ignore')

            cur_results = conn.execute(
                self._schema.trial_result.select().with_only_columns(
                    self._schema.trial_result.c.trial_id,
                    self._schema.trial_result.c.metric_id,
                    self._schema.trial_result.c.metric_value,
                ).where(
                    self._schema.trial_result.c.exp_id == self._exp_id,
                ).order_by(
                    self._schema.trial_result.c.trial_id,
                    self._schema.trial_result.c.metric_id,
                )
            )
            results_df = pandas.DataFrame(
                [(row.trial_id, "result." + row.metric_id, row.metric_value)
                 for row in cur_results.fetchall()],
                columns=['trial_id', 'metric', 'value']
            ).pivot(
                index="trial_id", columns="metric", values="value",
            ).apply(pandas.to_numeric, errors='ignore')

            return trials_df.merge(configs_df, on=["trial_id", "config_id"], how="left") \
                            .merge(results_df, on="trial_id", how="left")
