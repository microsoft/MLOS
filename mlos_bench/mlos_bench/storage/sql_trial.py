#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data in DB-API-compliant SQL database - the Trial part.
"""

import time
import logging

from mlos_bench.environment import Status
from mlos_bench.storage.base_storage import Storage

_LOG = logging.getLogger(__name__)


class Trial(Storage.Trial):
    """
    Storing the results of a single run of the experiment in SQL database.
    """

    def _update(self, table: str, timestamp: float, status: Status, value: dict = None):
        """
        Update the status of the trial and optionally add some results.

        Parameters
        ----------
        table: str
            The name of the table to store the results in.
            Must be either 'trial_telemetry' or 'trail_results'.
        timestamp: float
            The timestamp of the final results. (Use `None` for telemetry).
        status: Status
            The status of the trial.
        value: dict
            Pairs of (key, value): intermediate or final results of the trial.
        """
        _LOG.debug("Updating experiment run: %s", self)
        cursor = self._conn.cursor()
        cursor.execute("BEGIN")
        try:
            if value:
                cursor.executemany(
                    f"""
                    INSERT INTO {table} (exp_id, trial_id, param_id, param_value)
                    VALUES (?, ?, ?, ?)
                    """,
                    ((self._experiment_id, self._trial_id, key, val)
                        for (key, val) in value.items())
                )
            # FIXME: use the actual timestamp from the benchmark.
            cursor.execute(
                """
                UPDATE trial_status SET status = ?, ts_end = ?
                WHERE exp_id = ? AND trial_id = ?
                """,
                (status.name, timestamp, self._experiment_id, self._trial_id)
            )
            cursor.execute("COMMIT")
        except Exception:
            cursor.execute("ROLLBACK")
            raise

    def update(self, status: Status, value: dict = None):
        self._update("trial_results", time.time(), status, value)

    def update_telemetry(self, status: Status, value: dict = None):
        self._update("trial_telemetry", None, status, value)
