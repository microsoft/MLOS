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
from typing import Optional, Tuple, List, Dict, Iterator, Any

from sqlalchemy import Engine, Connection, Table, column, func

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql.schema import DbSchema
from mlos_bench.storage.sql.trial import Trial

_LOG = logging.getLogger(__name__)


class Experiment(Storage.Experiment):
    """
    Logic for retrieving and storing the results of a single experiment.
    """

    def __init__(self, *,
                 engine: Engine,
                 schema: DbSchema,
                 tunables: TunableGroups,
                 experiment_id: str,
                 trial_id: int,
                 root_env_config: str,
                 description: str,
                 opt_target: str):
        super().__init__(tunables, experiment_id, root_env_config)
        self._engine = engine
        self._schema = schema
        self._trial_id = trial_id
        self._description = description
        self._opt_target = opt_target

    def _setup(self) -> None:
        super()._setup()
        with self._engine.begin() as conn:
            # Get git info and the last trial ID for the experiment.
            # pylint: disable=not-callable
            exp_info = conn.execute(
                self._schema.experiment.select().with_only_columns(
                    self._schema.experiment.c.git_repo,
                    self._schema.experiment.c.git_commit,
                    self._schema.experiment.c.root_env_config,
                    func.max(self._schema.trial.c.trial_id).label("trial_id"),
                ).join(
                    self._schema.trial,
                    self._schema.trial.c.exp_id == self._schema.experiment.c.exp_id,
                    isouter=True
                ).where(
                    self._schema.experiment.c.exp_id == self._experiment_id,
                ).group_by(
                    self._schema.experiment.c.git_repo,
                    self._schema.experiment.c.git_commit,
                    self._schema.experiment.c.root_env_config,
                )
            ).fetchone()
            if exp_info is None:
                _LOG.info("Start new experiment: %s", self._experiment_id)
                # It's a new experiment: create a record for it in the database.
                conn.execute(self._schema.experiment.insert().values(
                    exp_id=self._experiment_id,
                    description=self._description,
                    git_repo=self._git_repo,
                    git_commit=self._git_commit,
                    root_env_config=self._root_env_config,
                ))
            else:
                if exp_info.trial_id is not None:
                    self._trial_id = exp_info.trial_id + 1
                _LOG.info("Continue experiment: %s last trial: %s resume from: %d",
                          self._experiment_id, exp_info.trial_id, self._trial_id)
                if exp_info.git_commit != self._git_commit:
                    _LOG.warning("Experiment %s git expected: %s %s",
                                 self, exp_info.git_repo, exp_info.git_commit)

    def merge(self, experiment_ids: List[str]) -> None:
        _LOG.info("Merge: %s <- %s", self._experiment_id, experiment_ids)
        raise NotImplementedError()

    def load(self, opt_target: Optional[str] = None) -> Tuple[List[dict], List[float]]:
        configs = []
        scores = []
        with self._engine.connect() as conn:
            cur_trials = conn.execute(
                self._schema.trial.select().with_only_columns(
                    self._schema.trial.c.trial_id,
                    self._schema.trial.c.config_id,
                    self._schema.trial_result.c.metric_value,
                ).join(
                    self._schema.trial_result, (
                        (self._schema.trial.c.exp_id == self._schema.trial_result.c.exp_id) &
                        (self._schema.trial.c.trial_id == self._schema.trial_result.c.trial_id)
                    )
                ).where(
                    self._schema.trial.c.status == 'SUCCEEDED',
                    self._schema.trial.c.exp_id == self._experiment_id,
                    self._schema.trial_result.c.metric_id == (opt_target or self._opt_target),
                ).order_by(
                    self._schema.trial.c.trial_id.asc(),
                )
            )
            for trial in cur_trials.fetchall():
                tunables = self._get_params(
                    conn, self._schema.config_param, config_id=trial.config_id)
                configs.append(tunables)
                scores.append(float(trial.metric_value))
            return (configs, scores)

    @staticmethod
    def _get_params(conn: Connection, table: Table, **kwargs: Any) -> Dict[str, Any]:
        cur_params = conn.execute(table.select().where(*[
            column(key) == val for (key, val) in kwargs.items()]))
        return {row.param_id: row.param_value for row in cur_params.fetchall()}

    @staticmethod
    def _save_params(conn: Connection, table: Table,
                     params: Dict[str, Any], **kwargs: Any) -> None:
        conn.execute(table.insert(), [
            {
                **kwargs,
                "param_id": key,
                "param_value": None if val is None else str(val)
            }
            for (key, val) in params.items()
        ])

    def pending_trials(self) -> Iterator[Storage.Trial]:
        _LOG.info("Retrieve pending trials for: %s", self._experiment_id)
        with self._engine.connect() as conn:
            cur_trials = conn.execute(self._schema.trial.select().where(
                self._schema.trial.c.exp_id == self._experiment_id,
                self._schema.trial.c.ts_end.is_(None)
            ))
            for trial in cur_trials.fetchall():
                tunables = self._get_params(
                    conn, self._schema.config_param,
                    config_id=trial.config_id)
                config = self._get_params(
                    conn, self._schema.trial_param,
                    exp_id=self._experiment_id, trial_id=trial.trial_id)
                yield Trial(
                    engine=self._engine,
                    schema=self._schema,
                    # Reset .is_updated flag after the assignment:
                    tunables=self._tunables.copy().assign(tunables).reset(),
                    experiment_id=self._experiment_id,
                    trial_id=trial.trial_id,
                    config_id=trial.config_id,
                    opt_target=self._opt_target,
                    config=config,
                )

    def _get_config_id(self, conn: Connection, tunables: TunableGroups) -> int:
        """
        Get the config ID for the given tunables. If the config does not exist,
        create a new record for it.
        """
        config_hash = hashlib.sha256(str(tunables).encode('utf-8')).hexdigest()
        cur_config = conn.execute(self._schema.config.select().where(
            self._schema.config.c.config_hash == config_hash
        )).fetchone()
        if cur_config is not None:
            return int(cur_config.config_id)  # mypy doesn't know it's always int
        # Config not found, create a new one:
        config_id: int = conn.execute(self._schema.config.insert().values(
            config_hash=config_hash)).inserted_primary_key[0]
        self._save_params(
            conn, self._schema.config_param,
            {tunable.name: tunable.value for (tunable, _group) in tunables},
            config_id=config_id)
        return config_id

    def new_trial(self, tunables: TunableGroups,
                  config: Optional[Dict[str, Any]] = None) -> Storage.Trial:
        _LOG.debug("Create trial: %s:%d", self._experiment_id, self._trial_id)
        with self._engine.begin() as conn:
            try:
                config_id = self._get_config_id(conn, tunables)
                conn.execute(self._schema.trial.insert().values(
                    exp_id=self._experiment_id,
                    trial_id=self._trial_id,
                    config_id=config_id,
                    ts_start=datetime.now(),
                    status='PENDING',
                ))
                if config is not None:
                    self._save_params(
                        conn, self._schema.trial_param, config,
                        exp_id=self._experiment_id, trial_id=self._trial_id)
                trial = Trial(
                    engine=self._engine,
                    schema=self._schema,
                    tunables=tunables,
                    experiment_id=self._experiment_id,
                    trial_id=self._trial_id,
                    config_id=config_id,
                    opt_target=self._opt_target,
                    config=config,
                )
                self._trial_id += 1
                return trial
            except Exception:
                conn.rollback()
                raise
