#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data in DB-API-compliant SQL database.
"""

import importlib
import logging

from mlos_bench.tunables import TunableGroups
from mlos_bench.storage import Storage

from mlos_bench.storage.sql_experiment import Experiment

_LOG = logging.getLogger(__name__)


class SqlStorage(Storage):
    """
    An implementation of the Storage interface for a DB-API-compliant database.
    """

    def __init__(self, tunables: TunableGroups, config: dict):
        super().__init__(tunables, config)
        module_name = self._config.pop("db_module")
        _LOG.debug("Using DB module: %s", module_name)
        self._db = importlib.import_module(module_name)

    def experiment(self):
        return Experiment(self._tunables, self._experiment_id, self._db, self._config)
