#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and updating benchmark data using SQLAlchemy backend.
"""

import logging
from datetime import datetime
from typing import Optional, Union, Dict, Any

from sqlalchemy import Engine, Table

from mlos_bench.environment import Status
from mlos_bench.tunables import TunableGroups
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql_schema import DbSchema

_LOG = logging.getLogger(__name__)


class Trial(Storage.Trial):
    """
    Store the results of a single run of the experiment in SQL database.
    """

    def __init__(self, engine: Engine, schema: DbSchema, tunables: TunableGroups,
                 experiment_id: str, trial_id: int, opt_target: str,
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(tunables, experiment_id, trial_id, opt_target, config)
        self._engine = engine
        self._schema = schema

    def _update(self, table: Table, timestamp: Optional[datetime],
                status: Status, value: Optional[Dict[str, Any]] = None) -> None:
        """
        Update the status of the trial and optionally add some results.

        Parameters
        ----------
        table: str
            The name of the table to store the results in.
            Must be either 'trial_telemetry' or 'trail_results'.
        timestamp: datetime
            The timestamp of the final results. (Use `None` for telemetry).
        status: Status
            The status of the trial.
        value: dict
            Pairs of (key, value): intermediate or final results of the trial.
        """
        _LOG.debug("Updating experiment run: %s", self)
        with self._engine.begin() as conn:
            try:
                # FIXME: Use the actual timestamp from the benchmark.
                conn.execute(
                    self._schema.trial.update().where(
                        self._schema.trial.c.exp_id == self._experiment_id,
                        self._schema.trial.c.trial_id == self._trial_id,
                    ).values(
                        status=status.name,
                        ts_end=timestamp,
                    )
                )
                # FIXME: Save timestamps for the telemetry data.
                if value:
                    conn.execute(table.insert().values([
                        {
                            "exp_id": self._experiment_id,
                            "trial_id": self._trial_id,
                            "metric_id": key,
                            "metric_value": None if val is None else str(val),
                        }
                        for (key, val) in value.items()
                    ]))
            except Exception:
                conn.rollback()
                raise

    def update(self, status: Status,
               value: Optional[Union[Dict[str, Any], Any]] = None
               ) -> Optional[Dict[str, Any]]:
        value = super().update(status, value)
        self._update(self._schema.trial_result, datetime.now(), status, value)
        return value

    def update_telemetry(self, status: Status, value: Optional[Dict[str, Any]] = None) -> None:
        super().update_telemetry(status, value)
        self._update(self._schema.trial_telemetry, None, status, value)
