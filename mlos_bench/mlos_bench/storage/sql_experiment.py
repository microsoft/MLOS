#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data in DB-API-compliant SQL database - the Experiment part.
"""

import logging
from typing import List

from mlos_bench.storage import Storage
from mlos_bench.tunables import TunableGroups

from mlos_bench.storage.sql_trial import Trial

_LOG = logging.getLogger(__name__)


class Experiment(Storage.Experiment):
    """
    Logic for retrieving and storing the results of a single experiment.
    """

    def __init__(self, db, connection_kwargs, experiment_id: str):
        super().__init__(experiment_id)
        self._db = db
        self._connection_kwargs = connection_kwargs
        self._conn = None
        self._last_trial_id = 0

    def __enter__(self):
        super().__enter__()
        self._conn = self._db.connect(**self._connection_kwargs)
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
            yield Trial(self._conn, new_tunables, self._experiment_id, trial_id)

    def trial(self, tunables: TunableGroups):
        self._last_trial_id += 1
        self._conn.execute(
            "INSERT INTO trial_status (exp_id, trial_id, status) VALUES (?, ?, 'PENDING')",
            (self._experiment_id, self._last_trial_id)
        )
        return Trial(self._conn, tunables, self._experiment_id, self._last_trial_id)
