#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data in DB-API-compliant SQL database.
"""

import time
import logging
from typing import List

import sqlite3

from mlos_bench.storage import Storage
from mlos_bench.environment import Status
from mlos_bench.tunables import TunableGroups

_LOG = logging.getLogger(__name__)


class SqlStorage(Storage):
    """
    An implementation of the Storage interface for a DB-API-compliant database.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        # FIXME: make it work for any DB-API connector
        self._db = sqlite3

    def experiment(self):
        return SqlStorage.Experiment(self, self._experiment_id)

    class Experiment(Storage.Experiment):
        """
        Logic for retrieving and storing the results of a single experiment.
        """

        def __init__(self, storage, experiment_id: str):
            super().__init__(storage, experiment_id)
            self._conn = None
            self._last_trial_id = 0

        def __enter__(self):
            super().__enter__()
            # FIXME: pass the connection parameters correctly
            self._conn = self._storage._db.connect(self._storage._config['db_path'])
            self._last_trial_id = self._conn.execute(
                "SELECT MAX(trial_id) FROM trial_status WHERE exp_id = ?",
                (self._experiment_id,)
            ).fetchone()[0] or 0
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self._conn:
                self._conn.close()
            return super().__exit__(exc_type, exc_val, exc_tb)

        def merge(self, experiment_ids: List[str]):
            _LOG.info("Merge: %s <- %s", self._experiment_id, experiment_ids)
            raise NotImplementedError()

        def load(self, opt_target: str) -> List[dict]:
            res = []
            cur_trials = self._conn.execute(
                """
                SELECT trial_id FROM trial_status
                WHERE exp_id = ? AND status = 'SUCCEEDED'
                """,
                (self._experiment_id,)
            )
            for (trial_id,) in cur_trials:
                tunables = self._get_tunables(trial_id)
                cur_score = self._conn.execute(
                    """
                    SELECT param_value FROM trial_results
                    WHERE exp_id = ? AND trial_id = ? AND param_id = ?
                    """,
                    (self._experiment_id, trial_id, opt_target)
                )
                score = cur_score.fetchone()[0]
                tunables[opt_target] = score
                res.append(tunables)
            return res

        def _get_tunables(self, trial_id: int) -> dict:
            return dict(self._conn.execute(
                """
                SELECT param_id, param_value FROM trial_config
                WHERE exp_id = ? AND trial_id = ?
                """,
                (self._experiment_id, trial_id)
            ).fetchall())

        def pending(self, tunables: TunableGroups):
            _LOG.info("Retrieve pending trials for: %s", self._experiment_id)
            cur_trials = self._conn.execute(
                "SELECT trial_id FROM trial_status WHERE exp_id = ? AND ts_end IS NULL",
                (self._experiment_id,)
            )
            for (trial_id,) in cur_trials:
                new_tunables = tunables.copy().assign(self._get_tunables(trial_id))
                yield SqlStorage.Trial(self._conn, new_tunables, self._experiment_id, trial_id)

        def trial(self, tunables: TunableGroups):
            self._last_trial_id += 1
            self._conn.execute(
                "INSERT INTO trial_status (exp_id, trial_id, status) VALUES (?, ?, 'PENDING')",
                (self._experiment_id, self._last_trial_id)
            )
            return SqlStorage.Trial(
                self._conn, tunables, self._experiment_id, self._last_trial_id)

    class Trial(Storage.Trial):
        """
        Storing the results of a single run of the experiment.
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
