#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Saving and restoring the benchmark data in DB-API-compliant SQL database.
"""

import logging

import sqlite3

from mlos_bench.storage import Storage

from mlos_bench.storage.sql_experiment import Experiment

_LOG = logging.getLogger(__name__)


class SqlStorage(Storage):
    """
    An implementation of the Storage interface for a DB-API-compliant database.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self._db = sqlite3
        self._connection_params = config.get("connection_params", {})

    def experiment(self):
        return Experiment(self._db, self._connection_params, self._experiment_id)
