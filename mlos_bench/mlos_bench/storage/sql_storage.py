#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base interface for saving and restoring the benchmark data.
"""

import logging
from typing import List

import sqlite3

from mlos_bench.storage import Storage
from mlos_bench.environment import Status
from mlos_bench.tunables import TunableGroups

_LOG = logging.getLogger(__name__)


class SqlStorage(Storage):
    """
    An implementation of the Storage interface for a DB-API-compliant database.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        # FIXME: make it work for any DB-API connector
        self._db = sqlite3

    def experiment(self):
        return SqlStorage.Experiment(self, self._experiment_id)

    class Experiment(Storage.Experiment):
        """
        Logic for retrieving and storing the results of a single experiment.
        """

        def __init__(self, storage, experiment_id: str):
            super().__init__(storage, experiment_id)
            self._conn = None

        def __enter__(self):
            super().__enter__()
            # FIXME: pass the connection parameters correctly
            self._conn = self._storage._db.connect(self._storage.config['db_path'])
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self._conn:
                self._conn.close()
            return super().__exit__(exc_type, exc_val, exc_tb)

        def merge(self, experiment_ids: List[str]):
            _LOG.info("Merge: %s <- %s", self._experiment_id, experiment_ids)
            raise NotImplementedError()

        def load(self) -> List[dict]:
            _LOG.info("Load experiment: %s", self._experiment_id)
            raise NotImplementedError()

        def pending(self):
            _LOG.info("Retrieve pending trials for: %s", self._experiment_id)
            return []

        def trial(self, tunables: TunableGroups):
            return SqlStorage.Trial(self._storage, tunables,
                                    self._experiment_id, self._trial_id)

    class Trial(Storage.Trial):
        """
        Storing the results of a single run of the experiment.
        """

        def __init__(self, storage, tunables: TunableGroups,
                     experiment_id: str, trial_id: int):
            super().__init__(storage, tunables, experiment_id, trial_id)
            _LOG.debug("Creating experiment run: %s", self)

        def __enter__(self):
            super().__enter__()
            _LOG.debug("Starting experiment run: %s", self)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            _LOG.debug("Finishing experiment run: %s", self)
            return super().__exit__(exc_type, exc_val, exc_tb)

        def __repr__(self) -> str:
            return f"{self._experiment_id}:{self._trial_id}"

        def update(self, status: Status, value: dict = None):
            _LOG.debug("Updating experiment run: %s", self)
            raise NotImplementedError()
