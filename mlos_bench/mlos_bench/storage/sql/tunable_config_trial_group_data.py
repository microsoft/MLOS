#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""An interface to access the tunable config trial group data stored in SQL DB."""

from typing import TYPE_CHECKING, Dict, Optional

import pandas
from sqlalchemy import Engine, Integer, func

from mlos_bench.storage.base_tunable_config_data import TunableConfigData
from mlos_bench.storage.base_tunable_config_trial_group_data import (
    TunableConfigTrialGroupData,
)
from mlos_bench.storage.sql import common
from mlos_bench.storage.sql.schema import DbSchema
from mlos_bench.storage.sql.tunable_config_data import TunableConfigSqlData

if TYPE_CHECKING:
    from mlos_bench.storage.base_trial_data import TrialData


class TunableConfigTrialGroupSqlData(TunableConfigTrialGroupData):
    """
    SQL interface for accessing the stored experiment benchmark tunable config trial
    group data.

    A (tunable) config is used to define an instance of values for a set of tunable
    parameters for a given experiment and can be used by one or more trial instances
    (e.g., for repeats), which we call a (tunable) config trial group.
    """

    def __init__(
        self,
        *,
        engine: Engine,
        schema: DbSchema,
        experiment_id: str,
        tunable_config_id: int,
        tunable_config_trial_group_id: Optional[int] = None,
    ):
        super().__init__(
            experiment_id=experiment_id,
            tunable_config_id=tunable_config_id,
            tunable_config_trial_group_id=tunable_config_trial_group_id,
        )
        self._engine = engine
        self._schema = schema

    def _get_tunable_config_trial_group_id(self) -> int:
        """Retrieve the trial's tunable_config_trial_group_id from the storage."""
        with self._engine.connect() as conn:
            tunable_config_trial_group = conn.execute(
                self._schema.trial.select()
                .with_only_columns(
                    func.min(self._schema.trial.c.trial_id)
                    .cast(Integer)
                    .label("tunable_config_trial_group_id"),  # pylint: disable=not-callable
                )
                .where(
                    self._schema.trial.c.exp_id == self._experiment_id,
                    self._schema.trial.c.config_id == self._tunable_config_id,
                )
                .group_by(
                    self._schema.trial.c.exp_id,
                    self._schema.trial.c.config_id,
                )
            )
            row = tunable_config_trial_group.fetchone()
            assert row is not None
            # pylint: disable=protected-access  # following DeprecationWarning in sqlalchemy
            return row._tuple()[0]

    @property
    def tunable_config(self) -> TunableConfigData:
        return TunableConfigSqlData(
            engine=self._engine,
            schema=self._schema,
            tunable_config_id=self.tunable_config_id,
        )

    @property
    def trials(self) -> Dict[int, "TrialData"]:
        """
        Retrieve the trials' data for this (tunable) config trial group from the
        storage.

        Returns
        -------
        trials : Dict[int, TrialData]
            A dictionary of the trials' data, keyed by trial id.
        """
        return common.get_trials(
            self._engine,
            self._schema,
            self._experiment_id,
            self._tunable_config_id,
        )

    @property
    def results_df(self) -> pandas.DataFrame:
        return common.get_results_df(
            self._engine,
            self._schema,
            self._experiment_id,
            self._tunable_config_id,
        )
