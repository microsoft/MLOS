#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data using SQLAlchemy.
"""

import logging
import hashlib
from datetime import datetime
from typing import Optional, List, Tuple

from sqlalchemy import text, column

from mlos_bench.tunables import TunableGroups
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql_trial import Trial

_LOG = logging.getLogger(__name__)

# This is to allow passing all required values to the Experiment constructor
# so that we don't have to expose the internals of the Storage class.
# This constructor is not visible to the user, so it's OK to disable the warning.
# pylint: disable=too-many-function-args,too-many-arguments


class Experiment(Storage.Experiment):
    """
    Logic for retrieving and storing the results of a single experiment.
    """

    def __init__(self, engine, schema, tunables: TunableGroups,
                 experiment_id: str, trial_id: int, description: str, opt_target: str):
        super().__init__(tunables, experiment_id, trial_id, description, opt_target)
        self._engine = engine
        self._schema = schema

    def __enter__(self):
        super().__enter__()
        with self._engine.begin() as conn:
            # Get git info and the last trial ID for the experiment.
            exp_info = conn.execute(
                text("""
                SELECT e.git_repo, e.git_commit, MAX(t.trial_id) AS trial_id
                FROM experiment AS e
                LEFT OUTER JOIN trial AS t ON (e.exp_id = t.exp_id)
                WHERE e.exp_id = :exp_id
                GROUP BY e.git_repo, e.git_commit
                """),
                {"exp_id": self._experiment_id}
            ).fetchone()
            if exp_info is None:
                _LOG.info("Start new experiment: %s", self._experiment_id)
                # It's a new experiment: create a record for it in the database.
                conn.execute(self._schema.experiment.insert().values(
                    exp_id=self._experiment_id,
                    description=self._description,
                    git_repo=self._git_repo,
                    git_commit=self._git_commit
                ))
            else:
                if exp_info.trial_id is not None:
                    self._trial_id = exp_info.trial_id + 1
                _LOG.info("Continue experiment: %s last trial: %s resume from: %d",
                          self._experiment_id, exp_info.trial_id, self._trial_id)
                if exp_info.git_commit != self._git_commit:
                    _LOG.warning("Experiment %s git expected: %s %s",
                                 self, exp_info.git_repo, exp_info.git_commit)
        return self

    def merge(self, experiment_ids: List[str]):
        _LOG.info("Merge: %s <- %s", self._experiment_id, experiment_ids)
        raise NotImplementedError()

    def load(self, opt_target: Optional[str] = None) -> Tuple[List[dict], List[float]]:
        configs = []
        scores = []
        with self._engine.connect() as conn:
            cur_trials = conn.execute(
                text("""
                SELECT t.trial_id, t.config_id, r.metric_value
                FROM trial AS t
                JOIN trial_result AS r ON (t.exp_id = r.exp_id AND t.trial_id = r.trial_id)
                WHERE t.exp_id = :exp_id AND t.status = 'SUCCEEDED' AND r.metric_id = :metric_id
                ORDER BY t.trial_id ASC
                """),
                {
                    "exp_id": self._experiment_id,
                    "metric_id": opt_target or self._opt_target
                }
            )
            for trial in cur_trials:
                tunables = self._get_params(
                    conn, self._schema.config_param, config_id=trial.config_id)
                configs.append(tunables)
                scores.append(float(trial.metric_value))
            return (configs, scores)

    @staticmethod
    def _get_params(conn, table, **kwargs) -> dict:
        cur_params = conn.execute(table.select().where(*[
            column(key) == val for (key, val) in kwargs.items()]))
        return {row.param_id: row.param_value for row in cur_params}

    @staticmethod
    def _save_params(conn, table, params: dict, **kwargs):
        conn.execute(table.insert(), [
            {
                **kwargs,
                "param_id": key,
                "param_value": None if val is None else str(val)
            }
            for (key, val) in params.items()
        ])

    def pending(self):
        _LOG.info("Retrieve pending trials for: %s", self._experiment_id)
        with self._engine.connect() as conn:
            cur_trials = conn.execute(self._schema.trial.select().where(
                column("exp_id") == self._experiment_id,
                column("ts_end").is_(None)
            ))
            for trial in cur_trials:
                tunables = self._get_params(
                    conn, self._schema.config_param,
                    config_id=trial.config_id)
                config = self._get_params(
                    conn, self._schema.trial_param,
                    exp_id=self._experiment_id, trial_id=trial.trial_id)
                # Reset .is_updated flag after the assignment:
                yield Trial(self._engine,
                            self._tunables.copy().assign(tunables).reset(),
                            self._experiment_id, trial.trial_id, self._opt_target, config)

    def _get_config_id(self, conn, tunables: TunableGroups) -> int:
        """
        Get the config ID for the given tunables. If the config does not exist,
        create a new record for it.
        """
        config_hash = hashlib.sha256(str(tunables).encode('utf-8')).hexdigest()
        cur_config = conn.execute(self._schema.config.select().where(
            column("config_hash") == config_hash
        )).fetchone()
        if cur_config is not None:
            return cur_config.config_id
        # Config not found, create a new one:
        config_id = conn.execute(self._schema.config.insert().values(
            config_hash=config_hash)).inserted_primary_key[0]
        self._save_params(
            conn, self._schema.config_param,
            {tunable.name: tunable.value for (tunable, _group) in tunables},
            config_id=config_id)
        return config_id

    def trial(self, tunables: TunableGroups, config: dict = None):
        _LOG.debug("Create trial: %s:%d", self._experiment_id, self._trial_id)
        with self._engine.begin() as conn:
            try:
                config_id = self._get_config_id(conn, tunables)
                conn.execute(self._schema.trial.insert().values(
                    exp_id=self._experiment_id,
                    trial_id=self._trial_id,
                    config_id=config_id,
                    ts_start=datetime.now(),
                    status='PENDING'
                ))
                if config is not None:
                    self._save_params(
                        conn, self._schema.trial_param, config,
                        exp_id=self._experiment_id, trial_id=self._trial_id)
                trial = Trial(self._engine, tunables, self._experiment_id,
                              self._trial_id, self._opt_target, config)
                self._trial_id += 1
                return trial
            except Exception:
                conn.rollback()
                raise
