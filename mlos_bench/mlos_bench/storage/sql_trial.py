#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data in DB-API-compliant SQL database - the Trial part.
"""

import time
import logging

from mlos_bench.storage import Storage
from mlos_bench.environment import Status

_LOG = logging.getLogger(__name__)


class Trial(Storage.Trial):
    """
    Storing the results of a single run of the experiment in SQL database.
    """

    def update(self, status: Status, value: dict = None):
        _LOG.debug("Updating experiment run: %s", self)
        cursor = self._conn.cursor()
        cursor.execute("BEGIN")
        try:
            if value:
                cursor.executemany(
                    """
                    INSERT INTO trial_results (exp_id, trial_id, param_id, param_value)
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
                (status.name, time.time(), self._experiment_id, self._trial_id)
            )
            cursor.execute("COMMIT")
        except Exception:
            cursor.execute("ROLLBACK")
            raise
