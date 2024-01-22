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
from sqlalchemy import Engine, Integer, func

from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.storage.base_trial_data import TrialData
from mlos_bench.storage.base_tunable_config_data import TunableConfigData
from mlos_bench.storage.base_tunable_config_trial_group_data import TunableConfigTrialGroupData
from mlos_bench.storage.sql import common
from mlos_bench.storage.sql.schema import DbSchema
from mlos_bench.storage.sql.tunable_config_data import TunableConfigSqlData
from mlos_bench.storage.sql.tunable_config_trial_group_data import TunableConfigTrialGroupSqlData

_LOG = logging.getLogger(__name__)


class ExperimentSqlData(ExperimentData):
    """
    Base interface for accessing the stored benchmark data.
    """

    def __init__(self, *,
                 engine: Engine,
                 schema: DbSchema,
                 experiment_id: str,
                 description: str,
                 root_env_config: str,
                 git_repo: str,
                 git_commit: str):
        super().__init__(
            experiment_id=experiment_id,
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
                        self._schema.objectives.c.exp_id == self._experiment_id,
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
            trial_objs_df = trial.metadata_df[
                trial.metadata_df["parameter"].isin(("opt_target", "opt_direction"))
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

    # TODO: provide a way to get individual data to avoid repeated bulk fetches where only small amounts of data is accessed.
    # Or else make the TrialData object lazily populate.

    @property
    def trials(self) -> Dict[int, TrialData]:
        return common.get_trials(self._engine, self._schema, self._experiment_id)

    @property
    def tunable_config_trial_groups(self) -> Dict[int, TunableConfigTrialGroupData]:
        with self._engine.connect() as conn:
            tunable_config_trial_groups = conn.execute(
                self._schema.trial.select().with_only_columns(
                    self._schema.trial.c.config_id,
                    func.min(self._schema.trial.c.trial_id).cast(Integer).label('tunable_config_trial_group_id'),
                ).where(
                    self._schema.trial.c.exp_id == self._experiment_id,
                ).group_by(
                    self._schema.trial.c.exp_id,
                    self._schema.trial.c.config_id,
                )
            )
            return {
                tunable_config_trial_group.config_id: TunableConfigTrialGroupSqlData(
                    engine=self._engine,
                    schema=self._schema,
                    experiment_id=self._experiment_id,
                    tunable_config_id=tunable_config_trial_group.config_id,
                    tunable_config_trial_group_id=tunable_config_trial_group.tunable_config_trial_group_id,
                )
                for tunable_config_trial_group in tunable_config_trial_groups.fetchall()
            }

    def tunable_configs(self) -> Dict[int, TunableConfigData]:
        with self._engine.connect() as conn:
            tunable_configs = conn.execute(
                self._schema.trial.select().with_only_columns(
                    self._schema.trial.c.config_id.cast(Integer).label('config_id'),
                ).where(
                    self._schema.trial.c.exp_id == self._experiment_id,
                ).group_by(
                    self._schema.trial.c.exp_id,
                    self._schema.trial.c.config_id,
                )
            )
            return {
                tunable_config.config_id: TunableConfigSqlData(
                    engine=self._engine,
                    schema=self._schema,
                    tunable_config_id=tunable_config.config_id,
                )
                for tunable_config in tunable_configs.fetchall()
            }

    @property
    def results_df(self) -> pandas.DataFrame:
        return common.get_results_df(self._engine, self._schema, self._experiment_id)
