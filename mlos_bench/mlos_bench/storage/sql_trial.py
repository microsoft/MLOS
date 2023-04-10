#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and updating benchmark data using SQLAlchemy backend.
"""

import logging
from datetime import datetime
from typing import Optional, Union, Dict

from sqlalchemy import text

from mlos_bench.environment import Status
from mlos_bench.storage.base_storage import Storage

_LOG = logging.getLogger(__name__)


class Trial(Storage.Trial):
    """
    Storing the results of a single run of the experiment in SQL database.
    """

    def _update(self, table: str, timestamp: datetime, status: Status, value: dict = None):
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
                    text("""
                        UPDATE trial SET status = :status, ts_end = :ts_end
                        WHERE exp_id = :exp_id AND trial_id = :trial_id
                    """),
                    {
                        "exp_id": self._experiment_id,
                        "trial_id": self._trial_id,
                        "status": status.name,
                        "ts_end": timestamp,
                    }
                )
                # FIXME: Save timestamps for the telemetry data.
                if value:
                    conn.execute(
                        text(f"""
                            INSERT INTO {table} (exp_id, trial_id, metric_id, metric_value)
                            VALUES (:exp_id, :trial_id, :metric_id, :metric_value)
                        """),
                        [
                            {
                                "exp_id": self._experiment_id,
                                "trial_id": self._trial_id,
                                "metric_id": key,
                                "metric_value": None if val is None else str(val),
                            }
                            for (key, val) in value.items()
                        ]
                    )
            except Exception:
                conn.rollback()
                raise

    def update(self, status: Status,
               value: Optional[Union[Dict[str, float], float]] = None
               ) -> Optional[Dict[str, float]]:
        value = super().update(status, value)
        self._update("trial_result", datetime.now(), status, value)

    def update_telemetry(self, status: Status, value: dict = None):
        super().update_telemetry(status, value)
        self._update("trial_telemetry", None, status, value)
