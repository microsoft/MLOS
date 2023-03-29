#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data in DB-API-compliant SQL database.
"""

import importlib
import logging

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
        module_name = self._config.pop("db_module")
        script_fname = self._config.pop("init_script", None)
        _LOG.debug("Import DB module: %s", module_name)
        db_mod = importlib.import_module(module_name)
        self._repr = f"{db_mod.__name__}:{self._config}"
        _LOG.info("Connect to the database: %s", self)
        self._conn = db_mod.connect(**self._config)
        if script_fname is not None:
            _LOG.info("Storage init script: %s", script_fname)
            with open(script_fname, encoding="utf-8") as script:
                self._conn.executescript(script.read())

    def __repr__(self) -> str:
        return self._repr

    def experiment(self):
        return Experiment(self._conn, self._tunables, self._experiment_id, self._trial_id)
