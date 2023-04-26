#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data in SQL database.
"""

import logging
from typing import Optional

from sqlalchemy import Engine, URL, create_engine

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.services.base_service import Service
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql.schema import DbSchema
from mlos_bench.storage.sql.experiment import Experiment

_LOG = logging.getLogger(__name__)


class SqlStorage(Storage):
    """
    An implementation of the Storage interface using SQLAlchemy backend.
    """

    def __init__(self, tunables: TunableGroups, service: Optional[Service], config: dict):
        super().__init__(tunables, service, config)
        lazy_schema_create = self._config.pop("lazy_schema_create", False)
        self._log_sql = self._config.pop("log_sql", False)
        self._url = URL.create(**self._config)
        self._repr = f"{self._url.get_backend_name()}:{self._url.database}"
        _LOG.info("Connect to the database: %s", self)
        self._engine = create_engine(self._url, echo=self._log_sql)
        self._db_schema: DbSchema
        if not lazy_schema_create:
            assert self._schema
        else:
            _LOG.info("Using lazy schema create for database: %s", self)

    @property
    def _schema(self) -> DbSchema:
        """Lazily create schema upon first access."""
        if not hasattr(self, '_db_schema'):
            self._db_schema = DbSchema(self._engine).create()
            if _LOG.isEnabledFor(logging.DEBUG):
                _LOG.debug("DDL statements:\n%s", self._schema)
        return self._db_schema

    def __repr__(self) -> str:
        return self._repr

    def experiment(self, *,
                   experiment_id: str,
                   trial_id: int,
                   root_env_config: str,
                   description: str,
                   opt_target: str) -> Storage.Experiment:
        return Experiment(
            engine=self._engine,
            schema=self._schema,
            tunables=self._tunables,
            experiment_id=experiment_id,
            trial_id=trial_id,
            root_env_config=root_env_config,
            description=description,
            opt_target=opt_target,
        )
