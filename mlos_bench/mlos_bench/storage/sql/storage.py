#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data in SQL database.
"""

import logging
from typing import Dict, Optional

from sqlalchemy import URL, create_engine

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.services.base_service import Service
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql.schema import DbSchema
from mlos_bench.storage.sql.experiment import Experiment
from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.storage.sql.experiment_data import ExperimentSqlData

_LOG = logging.getLogger(__name__)


class SqlStorage(Storage):
    """
    An implementation of the Storage interface using SQLAlchemy backend.
    """

    def __init__(self,
                 tunables: TunableGroups,
                 config: dict,
                 global_config: Optional[dict] = None,
                 service: Optional[Service] = None):
        super().__init__(tunables, config, global_config, service)
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
                   opt_target: str,
                   opt_direction: Optional[str]) -> Storage.Experiment:
        return Experiment(
            engine=self._engine,
            schema=self._schema,
            tunables=self._tunables,
            experiment_id=experiment_id,
            trial_id=trial_id,
            root_env_config=root_env_config,
            description=description,
            opt_target=opt_target,
            opt_direction=opt_direction,
        )

    @property
    def experiments(self) -> Dict[str, ExperimentData]:
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
                    exp_id=exp.exp_id,
                    description=exp.description,
                    root_env_config=exp.root_env_config,
                    git_repo=exp.git_repo,
                    git_commit=exp.git_commit,
                )
                for exp in cur_exp.fetchall()
            }
