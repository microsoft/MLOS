#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data in SQL database.
"""

import logging
from typing import Optional

from sqlalchemy import URL, create_engine

from mlos_bench.service import Service
from mlos_bench.tunables import TunableGroups
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql_schema import DbSchema
from mlos_bench.storage.sql_experiment import Experiment

_LOG = logging.getLogger(__name__)


class SqlStorage(Storage):
    """
    An implementation of the Storage interface using SQLAlchemy backend.
    """

    def __init__(self, tunables: TunableGroups, service: Optional[Service], config: dict):
        super().__init__(tunables, service, config)
        url = URL.create(**self._config)
        self._repr = f"{url.get_backend_name()}:{url.database}"
        _LOG.info("Connect to the database: %s", self)
        # Log SQL statements if the logging level is DEBUG:
        self._engine = create_engine(url)  # , echo=_LOG.isEnabledFor(logging.DEBUG))
        self._schema = DbSchema(self._engine).create()
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("DDL statements:\n%s", self._schema)

    def __repr__(self) -> str:
        return self._repr

    def experiment(self, experiment_id: str, trial_id: int,
                   description: str, opt_target: str) -> Storage.Experiment:
        return Experiment(
            engine=self._engine,
            schema=self._schema,
            tunables=self._tunables,
            experiment_id=experiment_id,
            trial_id=trial_id,
            description=description,
            opt_target=opt_target,
        )
