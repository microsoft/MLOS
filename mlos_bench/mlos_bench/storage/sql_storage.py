#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data in DB-API-compliant SQL database.
"""

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
                cur_tunables = self._conn.execute(
                    """
                    SELECT param_id, param_value FROM trial_config
                    WHERE exp_id = ? AND trial_id = ?
                    """,
                    (self._experiment_id, trial_id)
                )
                tunables = dict(cur_tunables.fetchall())
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

        def pending(self):
            _LOG.info("Retrieve pending trials for: %s", self._experiment_id)
            return []

        def trial(self, tunables: TunableGroups):
            self._last_trial_id += 1
            return SqlStorage.Trial(self._conn, tunables,
                                    self._experiment_id, self._last_trial_id)

    class Trial(Storage.Trial):
        """
        Storing the results of a single run of the experiment.
        """

        def __init__(self, conn, tunables: TunableGroups,
                     experiment_id: str, trial_id: int):
            super().__init__(conn, tunables, experiment_id, trial_id)
            _LOG.debug("Creating experiment run: %s", self)
            self._conn.execute(
                "INSERT INTO trial_status (exp_id, trial_id) VALUES (?, ?)",
                (self._experiment_id, self._trial_id)
            )

        def update(self, status: Status, value: dict = None):
            _LOG.debug("Updating experiment run: %s", self)
            raise NotImplementedError()
