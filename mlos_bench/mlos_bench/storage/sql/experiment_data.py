#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""An interface to access the experiment benchmark data stored in SQL DB."""
import logging
from typing import Dict, Literal, Optional

import pandas
from sqlalchemy import Engine, Integer, String, func

from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.storage.base_trial_data import TrialData
from mlos_bench.storage.base_tunable_config_data import TunableConfigData
from mlos_bench.storage.base_tunable_config_trial_group_data import (
    TunableConfigTrialGroupData,
)
from mlos_bench.storage.sql import common
from mlos_bench.storage.sql.schema import DbSchema
from mlos_bench.storage.sql.tunable_config_data import TunableConfigSqlData
from mlos_bench.storage.sql.tunable_config_trial_group_data import (
    TunableConfigTrialGroupSqlData,
)

_LOG = logging.getLogger(__name__)


class ExperimentSqlData(ExperimentData):
    """
    SQL interface for accessing the stored experiment benchmark data.

    An experiment groups together a set of trials that are run with a given set of
    scripts and mlos_bench configuration files.
    """

    def __init__(
        self,
        *,
        engine: Engine,
        schema: DbSchema,
        experiment_id: str,
        description: str,
        root_env_config: str,
        git_repo: str,
        git_commit: str,
    ):
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
    def objectives(self) -> Dict[str, Literal["min", "max"]]:
        with self._engine.connect() as conn:
            objectives_db_data = conn.execute(
                self._schema.objectives.select()
                .where(
                    self._schema.objectives.c.exp_id == self._experiment_id,
                )
                .order_by(
                    self._schema.objectives.c.weight.desc(),
                    self._schema.objectives.c.optimization_target.asc(),
                )
            )
            return {
                objective.optimization_target: objective.optimization_direction
                for objective in objectives_db_data.fetchall()
            }

    # TODO: provide a way to get individual data to avoid repeated bulk fetches
    # where only small amounts of data is accessed.
    # Or else make the TrialData object lazily populate.

    @property
    def trials(self) -> Dict[int, TrialData]:
        return common.get_trials(self._engine, self._schema, self._experiment_id)

    @property
    def tunable_config_trial_groups(self) -> Dict[int, TunableConfigTrialGroupData]:
        with self._engine.connect() as conn:
            tunable_config_trial_groups = conn.execute(
                self._schema.trial.select()
                .with_only_columns(
                    self._schema.trial.c.config_id,
                    func.min(self._schema.trial.c.trial_id)
                    .cast(Integer)
                    .label("tunable_config_trial_group_id"),  # pylint: disable=not-callable
                )
                .where(
                    self._schema.trial.c.exp_id == self._experiment_id,
                )
                .group_by(
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
                    tunable_config_trial_group_id=tunable_config_trial_group.tunable_config_trial_group_id,  # pylint:disable=line-too-long  # noqa
                )
                for tunable_config_trial_group in tunable_config_trial_groups.fetchall()
            }

    @property
    def tunable_configs(self) -> Dict[int, TunableConfigData]:
        with self._engine.connect() as conn:
            tunable_configs = conn.execute(
                self._schema.trial.select()
                .with_only_columns(
                    self._schema.trial.c.config_id.cast(Integer).label("config_id"),
                )
                .where(
                    self._schema.trial.c.exp_id == self._experiment_id,
                )
                .group_by(
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
    def default_tunable_config_id(self) -> Optional[int]:
        """
        Retrieves the (tunable) config id for the default tunable values for this
        experiment.

        Note: this is by *default* the first trial executed for this experiment.
        However, it is currently possible that the user changed the tunables config
        in between resumptions of an experiment.

        Returns
        -------
        int
        """
        with self._engine.connect() as conn:
            query_results = conn.execute(
                self._schema.trial.select()
                .with_only_columns(
                    self._schema.trial.c.config_id.cast(Integer).label("config_id"),
                )
                .where(
                    self._schema.trial.c.exp_id == self._experiment_id,
                    self._schema.trial.c.trial_id.in_(
                        self._schema.trial_param.select()
                        .with_only_columns(
                            func.min(self._schema.trial_param.c.trial_id)
                            .cast(Integer)
                            .label("first_trial_id_with_defaults"),  # pylint: disable=not-callable
                        )
                        .where(
                            self._schema.trial_param.c.exp_id == self._experiment_id,
                            self._schema.trial_param.c.param_id == "is_defaults",
                            func.lower(self._schema.trial_param.c.param_value, type_=String).in_(
                                ["1", "true"]
                            ),
                        )
                        .scalar_subquery()
                    ),
                )
            )
            min_default_trial_row = query_results.fetchone()
            if min_default_trial_row is not None:
                # pylint: disable=protected-access  # following DeprecationWarning in sqlalchemy
                return min_default_trial_row._tuple()[0]
            # fallback logic - assume minimum trial_id for experiment
            query_results = conn.execute(
                self._schema.trial.select()
                .with_only_columns(
                    self._schema.trial.c.config_id.cast(Integer).label("config_id"),
                )
                .where(
                    self._schema.trial.c.exp_id == self._experiment_id,
                    self._schema.trial.c.trial_id.in_(
                        self._schema.trial.select()
                        .with_only_columns(
                            func.min(self._schema.trial.c.trial_id)
                            .cast(Integer)
                            .label("first_trial_id"),
                        )
                        .where(
                            self._schema.trial.c.exp_id == self._experiment_id,
                        )
                        .scalar_subquery()
                    ),
                )
            )
            min_trial_row = query_results.fetchone()
            if min_trial_row is not None:
                # pylint: disable=protected-access  # following DeprecationWarning in sqlalchemy
                return min_trial_row._tuple()[0]
            return None

    @property
    def results_df(self) -> pandas.DataFrame:
        return common.get_results_df(self._engine, self._schema, self._experiment_id)
