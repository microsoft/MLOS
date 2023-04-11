#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data in SQL database.
"""

import logging

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

    def __init__(self, tunables: TunableGroups, service: Service, config: dict):
        super().__init__(tunables, service, config)
        url = URL.create(**self._config)
        self._repr = f"{url.get_backend_name()}:{url.database}"
        _LOG.info("Connect to the database: %s", self)
        self._engine = create_engine(url)  # , echo=True)
        self._schema = DbSchema(self._engine).create()

    def __repr__(self) -> str:
        return self._repr

    def experiment(self, exp_id: str, trial_id: int, description: str, opt_target: str):
        # pylint: disable=too-many-function-args
        return Experiment(self._engine, self._schema, self._tunables,
                          exp_id, trial_id, description, opt_target)
