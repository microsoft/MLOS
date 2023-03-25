#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data in DB-API-compliant SQL database - the Experiment part.
"""

import logging
from types import ModuleType
from typing import List, Tuple

from mlos_bench.tunables import TunableGroups
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql_trial import Trial

_LOG = logging.getLogger(__name__)


class Experiment(Storage.Experiment):
    """
    Logic for retrieving and storing the results of a single experiment.
    """

    def __init__(self, tunables: TunableGroups,
                 experiment_id: str, trial_id: int, db: ModuleType, config: dict):
        # pylint: disable=too-many-arguments
        super().__init__(tunables, experiment_id, trial_id)
        self._db = db
        self._config = config
        self._conn = None

    def __enter__(self):
        super().__enter__()
        _LOG.debug("Connecting to the database: %s with: %s", self._db.__name__, self._config)
        (git_repo, git_commit) = self._git_info()
        self._conn = self._db.connect(**self._config)
        (trial_id,) = self._conn.execute(
            "SELECT MAX(trial_id) FROM trial_status WHERE exp_id = ?",
            (self._experiment_id,)
        ).fetchone()
        if trial_id:
            self._trial_id = trial_id
        else:
            # TODO: check and store git repo and commit.
            self._conn.execute(
                """
                INSERT INTO experiment_config (exp_id, descr, git_repo, git_commit)
                VALUES (?, ?, ?, ?)
                """,
                (self._experiment_id, None, git_repo, git_commit)
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            self._conn.close()
        return super().__exit__(exc_type, exc_val, exc_tb)

    def merge(self, experiment_ids: List[str]):
        _LOG.info("Merge: %s <- %s", self._experiment_id, experiment_ids)
        raise NotImplementedError()

    def load(self, opt_target: str) -> Tuple[List[dict], List[float]]:
        configs = []
        scores = []
        cur_trials = self._conn.execute(
            """
            SELECT trial_id FROM trial_status
            WHERE exp_id = ? AND status = 'SUCCEEDED'
            """,
            (self._experiment_id,)
        )
        for (trial_id,) in cur_trials.fetchall():
            tunables = self._get_tunables(trial_id)
            cur_score = self._conn.execute(
                """
                SELECT param_value FROM trial_results
                WHERE exp_id = ? AND trial_id = ? AND param_id = ?
                """,
                (self._experiment_id, trial_id, opt_target)
            )
            configs.append(tunables)
            scores.append(cur_score.fetchone()[0])
        return (configs, scores)

    def _get_tunables(self, trial_id: int) -> dict:
        return dict(self._conn.execute(
            """
            SELECT param_id, param_value FROM trial_config
            WHERE exp_id = ? AND trial_id = ?
            """,
            (self._experiment_id, trial_id)
        ).fetchall())

    def pending(self):
        _LOG.info("Retrieve pending trials for: %s", self._experiment_id)
        cur_trials = self._conn.execute(
            "SELECT trial_id FROM trial_status WHERE exp_id = ? AND ts_end IS NULL",
            (self._experiment_id,)
        )
        for (trial_id,) in cur_trials.fetchall():
            tunables = self._tunables.copy().assign(self._get_tunables(trial_id))
            yield Trial(self._conn, tunables, self._experiment_id, trial_id)

    def trial(self, tunables: TunableGroups):
        _LOG.debug("Updating trial: %s:%d", self._experiment_id, self._trial_id)
        cursor = self._conn.cursor()
        cursor.execute("BEGIN")
        try:
            cursor.execute(
                """
                INSERT INTO trial_status (exp_id, trial_id, status)
                VALUES (?, ?, 'PENDING')
                """,
                (self._experiment_id, self._trial_id)
            )
            cursor.executemany(
                """
                INSERT INTO trial_config (exp_id, trial_id, param_id, param_value)
                VALUES (?, ?, ?, ?)
                """,
                ((self._experiment_id, self._trial_id, tunable.name,
                  str(tunable.value) if tunable.value is not None else None)
                 for (tunable, _group) in tunables)
            )
            trial = Trial(self._conn, tunables, self._experiment_id, self._trial_id)
            cursor.execute("COMMIT")
            self._trial_id += 1
            return trial
        except Exception:
            cursor.execute("ROLLBACK")
            raise
