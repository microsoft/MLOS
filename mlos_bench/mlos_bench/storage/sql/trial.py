#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
""":py:class:`.Storage.Trial` interface implementation for saving and restoring
the benchmark trial data using `SQLAlchemy <https://sqlalchemy.org>`_ backend.
"""


import logging
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal

from sqlalchemy import or_
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql.common import save_params
from mlos_bench.storage.sql.schema import DbSchema
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import nullable, utcify_timestamp

_LOG = logging.getLogger(__name__)


class Trial(Storage.Trial):
    """Store the results of a single run of the experiment in SQL database."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        engine: Engine,
        schema: DbSchema,
        tunables: TunableGroups,
        experiment_id: str,
        trial_id: int,
        config_id: int,
        trial_runner_id: int | None = None,
        opt_targets: dict[str, Literal["min", "max"]],
        config: dict[str, Any] | None = None,
    ):
        super().__init__(
            tunables=tunables,
            experiment_id=experiment_id,
            trial_id=trial_id,
            tunable_config_id=config_id,
            trial_runner_id=trial_runner_id,
            opt_targets=opt_targets,
            config=config,
        )
        self._engine = engine
        self._schema = schema

    def set_trial_runner(self, trial_runner_id: int) -> int:
        trial_runner_id = super().set_trial_runner(trial_runner_id)
        with self._engine.begin() as conn:
            conn.execute(
                self._schema.trial.update()
                .where(
                    self._schema.trial.c.exp_id == self._experiment_id,
                    self._schema.trial.c.trial_id == self._trial_id,
                    (
                        or_(
                            self._schema.trial.c.trial_runner_id.is_(None),
                            self._schema.trial.c.status == Status.PENDING.name,
                        )
                    ),
                )
                .values(
                    trial_runner_id=trial_runner_id,
                )
            )
        # Guard against concurrent updates.
        with self._engine.begin() as conn:
            trial_runner_rs = conn.execute(
                self._schema.trial.select()
                .with_only_columns(
                    self._schema.trial.c.trial_runner_id,
                )
                .where(
                    self._schema.trial.c.exp_id == self._experiment_id,
                    self._schema.trial.c.trial_id == self._trial_id,
                )
            )
            trial_runner_row = trial_runner_rs.fetchone()
            assert trial_runner_row
            self._trial_runner_id = trial_runner_row.trial_runner_id
            assert isinstance(self._trial_runner_id, int)
        return self._trial_runner_id

    def _save_new_config_data(self, new_config_data: Mapping[str, int | float | str]) -> None:
        with self._engine.begin() as conn:
            save_params(
                conn,
                self._schema.trial_param,
                new_config_data,
                exp_id=self._experiment_id,
                trial_id=self._trial_id,
            )

    def update(
        self,
        status: Status,
        timestamp: datetime,
        metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        # Make sure to convert the timestamp to UTC before storing it in the database.
        timestamp = utcify_timestamp(timestamp, origin="local")
        metrics = super().update(status, timestamp, metrics)
        with self._engine.begin() as conn:
            self._update_status(conn, status, timestamp)
            try:
                if status.is_completed():
                    # Final update of the status and ts_end:
                    cur_status = conn.execute(
                        self._schema.trial.update()
                        .where(
                            self._schema.trial.c.exp_id == self._experiment_id,
                            self._schema.trial.c.trial_id == self._trial_id,
                            self._schema.trial.c.ts_end.is_(None),
                            self._schema.trial.c.status.notin_(
                                ["SUCCEEDED", "CANCELED", "FAILED", "TIMED_OUT"]
                            ),
                        )
                        .values(
                            status=status.name,
                            ts_end=timestamp,
                        )
                    )
                    if cur_status.rowcount not in {1, -1}:
                        _LOG.warning("Trial %s :: update failed: %s", self, status)
                        raise RuntimeError(
                            f"Failed to update the status of the trial {self} to {status}. "
                            f"({cur_status.rowcount} rows)"
                        )
                    if metrics:
                        conn.execute(
                            self._schema.trial_result.insert().values(
                                [
                                    {
                                        "exp_id": self._experiment_id,
                                        "trial_id": self._trial_id,
                                        "metric_id": key,
                                        "metric_value": nullable(str, val),
                                    }
                                    for (key, val) in metrics.items()
                                ]
                            )
                        )
                else:
                    # Update of the status and ts_start when starting the trial:
                    assert metrics is None, f"Unexpected metrics for status: {status}"
                    cur_status = conn.execute(
                        self._schema.trial.update()
                        .where(
                            self._schema.trial.c.exp_id == self._experiment_id,
                            self._schema.trial.c.trial_id == self._trial_id,
                            self._schema.trial.c.ts_end.is_(None),
                            self._schema.trial.c.status.notin_(
                                ["RUNNING", "SUCCEEDED", "CANCELED", "FAILED", "TIMED_OUT"]
                            ),
                        )
                        .values(
                            status=status.name,
                            ts_start=timestamp,
                        )
                    )
                    if cur_status.rowcount not in {1, -1}:
                        # Keep the old status and timestamp if already running, but log it.
                        _LOG.warning("Trial %s :: cannot be updated to: %s", self, status)
            except Exception:
                conn.rollback()
                raise
        return metrics

    def update_telemetry(
        self,
        status: Status,
        timestamp: datetime,
        metrics: list[tuple[datetime, str, Any]],
    ) -> None:
        super().update_telemetry(status, timestamp, metrics)
        # Make sure to convert the timestamp to UTC before storing it in the database.
        timestamp = utcify_timestamp(timestamp, origin="local")
        metrics = [(utcify_timestamp(ts, origin="local"), key, val) for (ts, key, val) in metrics]
        # NOTE: Not every SQLAlchemy dialect supports `Insert.on_conflict_do_nothing()`
        # and we need to keep `.update_telemetry()` idempotent; hence a loop instead of
        # a bulk upsert.
        # See Also: comments in <https://github.com/microsoft/MLOS/pull/466>
        with self._engine.begin() as conn:
            self._update_status(conn, status, timestamp)
        for metric_ts, key, val in metrics:
            with self._engine.begin() as conn:
                try:
                    conn.execute(
                        self._schema.trial_telemetry.insert().values(
                            exp_id=self._experiment_id,
                            trial_id=self._trial_id,
                            ts=metric_ts,
                            metric_id=key,
                            metric_value=nullable(str, val),
                        )
                    )
                except IntegrityError as ex:
                    _LOG.warning("Record already exists: %s :: %s", (metric_ts, key, val), ex)

    def _update_status(self, conn: Connection, status: Status, timestamp: datetime) -> None:
        """
        Insert a new status record into the database.

        This call is idempotent.
        """
        # Make sure to convert the timestamp to UTC before storing it in the database.
        timestamp = utcify_timestamp(timestamp, origin="local")
        try:
            conn.execute(
                self._schema.trial_status.insert().values(
                    exp_id=self._experiment_id,
                    trial_id=self._trial_id,
                    ts=timestamp,
                    status=status.name,
                )
            )
        except IntegrityError as ex:
            _LOG.warning(
                "Status with that timestamp already exists: %s %s :: %s",
                self,
                timestamp,
                ex,
            )
