#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and updating benchmark data using SQLAlchemy backend.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple, Union, Dict, Any

from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError

from mlos_bench.environments.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql.schema import DbSchema

_LOG = logging.getLogger(__name__)


class Trial(Storage.Trial):
    """
    Store the results of a single run of the experiment in SQL database.
    """

    def __init__(self, *,
                 engine: Engine, schema: DbSchema, tunables: TunableGroups,
                 experiment_id: str, trial_id: int, config_id: int,
                 opt_target: str, opt_direction: Optional[str],
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(
            tunables=tunables,
            experiment_id=experiment_id,
            trial_id=trial_id,
            config_id=config_id,
            opt_target=opt_target,
            opt_direction=opt_direction,
            config=config,
        )
        self._engine = engine
        self._schema = schema

    def update(self, status: Status, timestamp: datetime,
               metrics: Optional[Union[Dict[str, Any], float]] = None
               ) -> Optional[Dict[str, Any]]:
        metrics = super().update(status, timestamp, metrics)
        with self._engine.begin() as conn:
            try:
                cur_status = conn.execute(
                    self._schema.trial.update().where(
                        self._schema.trial.c.exp_id == self._experiment_id,
                        self._schema.trial.c.trial_id == self._trial_id,
                        self._schema.trial.c.status.notin_(
                            ['SUCCEEDED', 'CANCELED', 'FAILED', 'TIMED_OUT']),
                    ).values(
                        status=status.name,
                        ts_end=timestamp,
                    )
                )
                if cur_status.rowcount not in {1, -1}:
                    _LOG.warning("Trial %s :: update failed: %s", self, status)
                    raise RuntimeError(
                        f"Failed to update the status of the trial {self} to {status}." +
                        f" ({cur_status.rowcount} rows)")
                if metrics:
                    conn.execute(self._schema.trial_result.insert().values([
                        {
                            "exp_id": self._experiment_id,
                            "trial_id": self._trial_id,
                            "metric_id": key,
                            "metric_value": None if val is None else str(val),
                        }
                        for (key, val) in metrics.items()
                    ]))
            except Exception:
                conn.rollback()
                raise

        return metrics

    def update_telemetry(self, status: Status, metrics: List[Tuple[datetime, str, Any]]) -> None:
        super().update_telemetry(status, metrics)
        # NOTE: Not every SQLAlchemy dialect supports `Insert.on_conflict_do_nothing()`
        # and we need to keep `.update_telemetry()` idempotent; hence a loop instead of
        # a bulk upsert.
        # See Also: comments in <https://github.com/microsoft/MLOS/pull/466>
        for (timestamp, key, val) in metrics:
            with self._engine.begin() as conn:
                try:
                    conn.execute(self._schema.trial_telemetry.insert().values(
                        exp_id=self._experiment_id,
                        trial_id=self._trial_id,
                        ts=timestamp,
                        metric_id=key,
                        metric_value=None if val is None else str(val),
                    ))
                except IntegrityError as ex:
                    _LOG.warning("Record already exists: %s :: %s", (timestamp, key, val), ex)
