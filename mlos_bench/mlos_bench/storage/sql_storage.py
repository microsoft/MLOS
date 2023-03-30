#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data in DB-API-compliant SQL database.
"""

import logging

from sqlalchemy import URL, create_engine, text

from mlos_bench.service import Service
from mlos_bench.tunables import TunableGroups
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql_experiment import Experiment

_LOG = logging.getLogger(__name__)


class SqlStorage(Storage):
    """
    An implementation of the Storage interface for a DB-API-compliant database.
    """

    def __init__(self, tunables: TunableGroups, service: Service, config: dict):

        super().__init__(tunables, service, config)
        script_fname = self._config.pop("init_script", None)

        url = URL.create(**self._config)
        self._repr = f"{url.get_backend_name()}:{url.database}"
        _LOG.info("Connect to the database: %s", self)

        self._engine = create_engine(url)  # , echo=True)

        if script_fname is not None:
            _LOG.info("Storage init script: %s", script_fname)
            with self._engine.begin() as conn, \
                 open(script_fname, encoding="utf-8") as script:
                script_lines = script.read()
                if self._engine.dialect.name in {"sqlite", "duckdb"}:
                    conn.connection.executescript(script_lines)
                else:
                    conn.execute(text(script_lines))

    def __repr__(self) -> str:
        return self._repr

    def experiment(self):
        return Experiment(self._engine, self._tunables,
                          self._experiment_id, self._trial_id)
