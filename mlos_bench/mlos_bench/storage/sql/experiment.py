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
from typing import Optional, Tuple, List, Literal, Dict, Iterator, Any

from pytz import UTC

from sqlalchemy import Engine, Connection, CursorResult, Table, column, func, select

from mlos_bench.environments.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql.schema import DbSchema
from mlos_bench.storage.sql.trial import Trial
from mlos_bench.util import nullable, utcify_timestamp

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
                 opt_targets: Dict[str, Literal['min', 'max']]):
        super().__init__(
            tunables=tunables,
            experiment_id=experiment_id,
            trial_id=trial_id,
            root_env_config=root_env_config,
            description=description,
            opt_targets=opt_targets,
        )
        self._engine = engine
        self._schema = schema

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
                conn.execute(self._schema.objectives.insert().values([
                    {
                        "exp_id": self._experiment_id,
                        "optimization_target": opt_target,
                        "optimization_direction": opt_dir,
                    }
                    for (opt_target, opt_dir) in self.opt_targets.items()
                ]))
            else:
                if exp_info.trial_id is not None:
                    self._trial_id = exp_info.trial_id + 1
                _LOG.info("Continue experiment: %s last trial: %s resume from: %d",
                          self._experiment_id, exp_info.trial_id, self._trial_id)
                # TODO: Sanity check that certain critical configs (e.g.,
                # objectives) haven't changed to be incompatible such that a new
                # experiment should be started (possibly by prewarming with the
                # previous one).
                if exp_info.git_commit != self._git_commit:
                    _LOG.warning("Experiment %s git expected: %s %s",
                                 self, exp_info.git_repo, exp_info.git_commit)

    def merge(self, experiment_ids: List[str]) -> None:
        _LOG.info("Merge: %s <- %s", self._experiment_id, experiment_ids)
        raise NotImplementedError("TODO")

    def load_tunable_config(self, config_id: int) -> Dict[str, Any]:
        with self._engine.connect() as conn:
            return self._get_key_val(conn, self._schema.config_param, "param", config_id=config_id)

    def load_telemetry(self, trial_id: int) -> List[Tuple[datetime, str, Any]]:
        with self._engine.connect() as conn:
            cur_telemetry = conn.execute(
                self._schema.trial_telemetry.select().where(
                    self._schema.trial_telemetry.c.exp_id == self._experiment_id,
                    self._schema.trial_telemetry.c.trial_id == trial_id
                ).order_by(
                    self._schema.trial_telemetry.c.ts,
                    self._schema.trial_telemetry.c.metric_id,
                )
            )
            # Not all storage backends store the original zone info.
            # We try to ensure data is entered in UTC and augment it on return again here.
            return [(utcify_timestamp(row.ts, origin="utc"), row.metric_id, row.metric_value)
                    for row in cur_telemetry.fetchall()]

    def load(self, last_trial_id: int = -1,
             ) -> Tuple[List[int], List[dict], List[Optional[Dict[str, Any]]], List[Status]]:

        with self._engine.connect() as conn:
            cur_trials = conn.execute(
                self._schema.trial.select().with_only_columns(
                    self._schema.trial.c.trial_id,
                    self._schema.trial.c.config_id,
                    self._schema.trial.c.status,
                ).where(
                    self._schema.trial.c.exp_id == self._experiment_id,
                    self._schema.trial.c.trial_id > last_trial_id,
                    self._schema.trial.c.status.in_(['SUCCEEDED', 'FAILED', 'TIMED_OUT']),
                ).order_by(
                    self._schema.trial.c.trial_id.asc(),
                )
            )

            trial_ids: List[int] = []
            configs: List[Dict[str, Any]] = []
            scores: List[Optional[Dict[str, Any]]] = []
            status: List[Status] = []

            for trial in cur_trials.fetchall():
                stat = Status[trial.status]
                status.append(stat)
                trial_ids.append(trial.trial_id)
                configs.append(self._get_key_val(
                    conn, self._schema.config_param, "param", config_id=trial.config_id))
                if stat.is_succeeded():
                    scores.append(self._get_key_val(
                        conn, self._schema.trial_result, "metric",
                        exp_id=self._experiment_id, trial_id=trial.trial_id))
                else:
                    scores.append(None)

            return (trial_ids, configs, scores, status)

    @staticmethod
    def _get_key_val(conn: Connection, table: Table, field: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Helper method to retrieve key-value pairs from the database.
        (E.g., configurations, results, and telemetry).
        """
        cur_result: CursorResult[Tuple[str, Any]] = conn.execute(
            select(
                column(f"{field}_id"),
                column(f"{field}_value"),
            ).select_from(table).where(
                *[column(key) == val for (key, val) in kwargs.items()]
            )
        )
        # NOTE: `Row._tuple()` is NOT a protected member; the class uses `_` to avoid naming conflicts.
        return dict(row._tuple() for row in cur_result.fetchall())  # pylint: disable=protected-access

    @staticmethod
    def _save_params(conn: Connection, table: Table,
                     params: Dict[str, Any], **kwargs: Any) -> None:
        if not params:
            return
        conn.execute(table.insert(), [
            {
                **kwargs,
                "param_id": key,
                "param_value": nullable(str, val)
            }
            for (key, val) in params.items()
        ])

    def pending_trials(self, timestamp: datetime, *, running: bool) -> Iterator[Storage.Trial]:
        timestamp = utcify_timestamp(timestamp, origin="local")
        _LOG.info("Retrieve pending trials for: %s @ %s", self._experiment_id, timestamp)
        if running:
            pending_status = ['PENDING', 'READY', 'RUNNING']
        else:
            pending_status = ['PENDING']
        with self._engine.connect() as conn:
            cur_trials = conn.execute(self._schema.trial.select().where(
                self._schema.trial.c.exp_id == self._experiment_id,
                (self._schema.trial.c.ts_start.is_(None) |
                 (self._schema.trial.c.ts_start <= timestamp)),
                self._schema.trial.c.ts_end.is_(None),
                self._schema.trial.c.status.in_(pending_status),
            ))
            for trial in cur_trials.fetchall():
                tunables = self._get_key_val(
                    conn, self._schema.config_param, "param",
                    config_id=trial.config_id)
                config = self._get_key_val(
                    conn, self._schema.trial_param, "param",
                    exp_id=self._experiment_id, trial_id=trial.trial_id)
                yield Trial(
                    engine=self._engine,
                    schema=self._schema,
                    # Reset .is_updated flag after the assignment:
                    tunables=self._tunables.copy().assign(tunables).reset(),
                    experiment_id=self._experiment_id,
                    trial_id=trial.trial_id,
                    config_id=trial.config_id,
                    opt_targets=self._opt_targets,
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

    def new_trial(self, tunables: TunableGroups, ts_start: Optional[datetime] = None,
                  config: Optional[Dict[str, Any]] = None) -> Storage.Trial:
        # MySQL can round microseconds into the future causing scheduler to skip trials.
        # Truncate microseconds to avoid this issue.
        ts_start = utcify_timestamp(ts_start or datetime.now(UTC), origin="local").replace(microsecond=0)
        _LOG.debug("Create trial: %s:%d @ %s", self._experiment_id, self._trial_id, ts_start)
        with self._engine.begin() as conn:
            try:
                config_id = self._get_config_id(conn, tunables)
                conn.execute(self._schema.trial.insert().values(
                    exp_id=self._experiment_id,
                    trial_id=self._trial_id,
                    config_id=config_id,
                    ts_start=ts_start,
                    status='PENDING',
                ))

                # Note: config here is the framework config, not the target
                # environment config (i.e., tunables).
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
                    opt_targets=self._opt_targets,
                    config=config,
                )
                self._trial_id += 1
                return trial
            except Exception:
                conn.rollback()
                raise
