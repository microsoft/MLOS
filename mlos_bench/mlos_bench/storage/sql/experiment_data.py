#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
An interface to access the benchmark data stored in SQL DB.
"""
from typing import Dict

import logging

import pandas
from sqlalchemy import Engine

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.storage.sql.schema import DbSchema
from mlos_bench.storage.base_trial_data import TrialData
from mlos_bench.storage.sql.trial_data import TrialSqlData

_LOG = logging.getLogger(__name__)


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
    def objectives(self) -> Dict[str, str]:
        objectives: Dict[str, str] = {}
        # First try to lookup the objectives from the experiment metadata in the storage layer.
        if hasattr(self._schema, "objectives"):
            with self._engine.connect() as conn:
                objectives_db_data = conn.execute(
                    self._schema.objectives.select().where(
                        self._schema.objectives.c.exp_id == self._exp_id,
                    ).order_by(
                        self._schema.objectives.c.weight.desc(),
                        self._schema.objectives.c.optimization_target.asc(),
                    )
                )
                objectives = {
                    objective.optimization_target: objective.optimization_direction
                    for objective in objectives_db_data.fetchall()
                }
        # Backwards compatibility: try and obtain the objectives from the TrialData and merge them in.
        # NOTE: The original format of storing opt_target/opt_direction in the Trial
        # metadata did not support multi-objectives.
        # Nor does it make it easy to detect when a config change caused a switch in
        # opt_direction for a given opt_target between run.py executions of an
        # Experiment.
        # For now, we simply issue a warning about potentially inconsistent data.
        for trial in self.trials.values():
            trial_objs_df = trial.metadata[
                trial.metadata["parameter"].isin(("opt_target", "opt_direction"))
            ][["parameter", "value"]]
            try:
                opt_targets = trial_objs_df[trial_objs_df["parameter"] == "opt_target"]
                assert len(opt_targets) == 1, \
                    "Should only be a single opt_target in the metadata params."
                opt_target = opt_targets["value"].iloc[0]
            except KeyError:
                continue
            try:
                opt_directions = trial_objs_df[trial_objs_df["parameter"] == "opt_direction"]
                assert len(opt_directions) <= 1, \
                    "Should only be a single opt_direction in the metadata params."
                opt_direction = opt_directions["value"].iloc[0]
            except (KeyError, IndexError):
                opt_direction = None
            if opt_target not in objectives:
                objectives[opt_target] = opt_direction
            elif opt_direction != objectives[opt_target]:
                _LOG.warning("Experiment %s has multiple trial optimization directions for optimization_target %s=%s",
                             self, opt_target, objectives[opt_target])
        return objectives

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
                [(row.trial_id, row.config_id, self.CONFIG_COLUMN_PREFIX + row.param_id, row.param_value)
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
                [(row.trial_id, self.RESULT_COLUMN_PREFIX + row.metric_id, row.metric_value)
                 for row in cur_results.fetchall()],
                columns=['trial_id', 'metric', 'value']
            ).pivot(
                index="trial_id", columns="metric", values="value",
            ).apply(pandas.to_numeric, errors='ignore')

            return trials_df.merge(configs_df, on=["trial_id", "config_id"], how="left") \
                            .merge(results_df, on="trial_id", how="left")
