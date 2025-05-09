#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Saving and restoring the benchmark data in SQL database."""

import logging
from typing import Literal

from sqlalchemy import URL, Engine, create_engine

from mlos_bench.services.base_service import Service
from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql.experiment import Experiment
from mlos_bench.storage.sql.experiment_data import ExperimentSqlData
from mlos_bench.storage.sql.schema import DbSchema
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class SqlStorage(Storage):
    """An implementation of the :py:class:`~.Storage` interface using SQLAlchemy
    backend.
    """

    def __init__(
        self,
        config: dict,
        global_config: dict | None = None,
        service: Service | None = None,
    ):
        super().__init__(config, global_config, service)
        self._lazy_schema_create = self._config.pop("lazy_schema_create", False)
        self._log_sql = self._config.pop("log_sql", False)
        self._url = URL.create(**self._config)
        self._repr = f"{self._url.get_backend_name()}:{self._url.database}"
        self._engine: Engine
        self._db_schema: DbSchema
        self._schema_created = False
        self._schema_updated = False
        self._init_engine()

    def _init_engine(self) -> None:
        """Initialize the SQLAlchemy engine."""
        # This is a no-op, as the engine is created in __init__.
        _LOG.info("Connect to the database: %s", self)
        self._engine = create_engine(self._url, echo=self._log_sql)
        self._db_schema = DbSchema(self._engine)
        if not self._lazy_schema_create:
            assert self._schema
            self.update_schema()
        else:
            _LOG.info("Using lazy schema create for database: %s", self)

    # Make the object picklable.

    def __getstate__(self) -> dict:
        """Return the state of the object for pickling."""
        state = self.__dict__.copy()
        # Don't pickle the engine, as it cannot be pickled.
        state.pop("_engine", None)
        state.pop("_db_schema", None)
        return state

    def __setstate__(self, state: dict) -> None:
        """Restore the state of the object from pickling."""
        self.__dict__.update(state)
        # Recreate the engine and schema.
        self._init_engine()

    @property
    def _schema(self) -> DbSchema:
        """Lazily create schema upon first access."""
        if not self._schema_created:
            self._db_schema.create()
            self._schema_created = True
            if _LOG.isEnabledFor(logging.DEBUG):
                _LOG.debug("DDL statements:\n%s", self._db_schema)
        return self._db_schema

    def update_schema(self) -> None:
        """Update the database schema."""
        if not self._schema_updated:
            self._schema.update()
            self._schema_updated = True

    def __repr__(self) -> str:
        return self._repr

    def get_experiment_by_id(
        self,
        experiment_id,
        tunables: TunableGroups,
        opt_targets: dict[str, Literal["min", "max"]],
    ) -> Storage.Experiment | None:
        with self._engine.connect() as conn:
            cur_exp = conn.execute(
                self._schema.experiment.select().where(
                    self._schema.experiment.c.exp_id == experiment_id,
                )
            )
            exp = cur_exp.fetchone()
            if exp is None:
                return None
            return Experiment(
                engine=self._engine,
                schema=self._schema,
                experiment_id=exp.exp_id,
                trial_id=-1,  # will be loaded upon __enter__ which calls _setup()
                description=exp.description,
                root_env_config=exp.root_env_config,
                tunables=tunables,
                opt_targets=opt_targets,
            )

    def experiment(  # pylint: disable=too-many-arguments
        self,
        *,
        experiment_id: str,
        trial_id: int,
        root_env_config: str,
        description: str,
        tunables: TunableGroups,
        opt_targets: dict[str, Literal["min", "max"]],
    ) -> Storage.Experiment:
        return Experiment(
            engine=self._engine,
            schema=self._schema,
            tunables=tunables,
            experiment_id=experiment_id,
            trial_id=trial_id,
            root_env_config=root_env_config,
            description=description,
            opt_targets=opt_targets,
        )

    @property
    def experiments(self) -> dict[str, ExperimentData]:
        # FIXME: this is somewhat expensive if only fetching a single Experiment.
        # May need to expand the API or data structures to lazily fetch data and/or cache it.
        with self._engine.connect() as conn:
            cur_exp = conn.execute(
                self._schema.experiment.select().order_by(
                    self._schema.experiment.c.exp_id.asc(),
                )
            )
            return {
                exp.exp_id: ExperimentSqlData(
                    engine=self._engine,
                    schema=self._schema,
                    experiment_id=exp.exp_id,
                    description=exp.description,
                    root_env_config=exp.root_env_config,
                    git_repo=exp.git_repo,
                    git_commit=exp.git_commit,
                )
                for exp in cur_exp.fetchall()
            }
