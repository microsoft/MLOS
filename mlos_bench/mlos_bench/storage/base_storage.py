#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base interface for saving and restoring the benchmark data.
"""

import logging
from abc import ABCMeta, abstractmethod
from typing import List, Tuple

from mlos_bench.environment import Status
from mlos_bench.service import Service
from mlos_bench.tunables import TunableGroups
from mlos_bench.util import get_git_info

_LOG = logging.getLogger(__name__)


class Storage(metaclass=ABCMeta):
    """
    An abstract interface between the benchmarking framework
    and storage systems (e.g., SQLite or MLFLow).
    """

    def __init__(self, tunables: TunableGroups, service: Service, config: dict):
        """
        Create a new storage object.

        Parameters
        ----------
        tunables : TunableGroups
            Tunable parameters of the environment. We need them to validate the
            configurations of merged-in experiments and restored/pending trials.
        config : dict
            Free-format key/value pairs of configuration parameters.
        """
        _LOG.debug("Storage config: %s", config)
        self._tunables = tunables.copy()
        self._service = service
        self._config = config.copy()
        self._experiment_id = self._config.pop("experimentId").strip()
        self._trial_id = int(self._config.pop("trialId", 0))

    @property
    def experiment_id(self) -> str:
        """
        String ID of the experiment being stored.
        """
        return self._experiment_id

    @abstractmethod
    def experiment(self):
        """
        Create a new experiment in the storage.

        Returns
        -------
        experiment : Storage.Experiment
            An object that allows to update the storage with
            the results of the experiment and related data.
        """

    class Experiment(metaclass=ABCMeta):
        """
        Base interface for storing the results of the experiment.
        This class is instantiated in the `Storage.experiment()` method.
        """

        def __init__(self, conn, tunables: TunableGroups, experiment_id: str, trial_id: int = 0):
            self._conn = conn
            self._tunables = tunables  # No need to copy, it's immutable
            self._experiment_id = experiment_id
            self._trial_id = trial_id
            (self._git_repo, self._git_commit) = get_git_info()

        def __enter__(self):
            """
            Enter the context of the experiment.
            """
            _LOG.debug("Starting experiment: %s", self)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            """
            End the context of the experiment.
            """
            if exc_val is None:
                _LOG.debug("Finishing experiment: %s", self)
            else:
                _LOG.warning("Finishing experiment: %s", self,
                             exc_info=(exc_type, exc_val, exc_tb))
            return False  # Do not suppress exceptions

        def __repr__(self) -> str:
            return self._experiment_id

        @abstractmethod
        def merge(self, experiment_ids: List[str]):
            """
            Merge in the results of other experiments.

            Parameters
            ----------
            experiment_ids : List[str]
                List of IDs of the experiments to merge in.
            """

        @abstractmethod
        def load(self, opt_target: str) -> Tuple[List[dict], List[float]]:
            """
            Load (tunable values, benchmark scores) to warm-up the optimizer.
            This call returns data from ALL merged-in experiments and attempts
            to impute the missing tunable values.
            """

        @abstractmethod
        def pending(self):
            """
            Return an iterator over the pending experiment runs.
            """

        @abstractmethod
        def trial(self, tunables: TunableGroups):
            """
            Create a new experiment run in the storage.

            Parameters
            ----------
            tunables : TunableGroups
                Tunable parameters of the experiment.

            Returns
            -------
            trial : Storage.Trial
                An object that allows to update the storage with
                the results of the experiment run.
            """

    class Trial(metaclass=ABCMeta):
        """
        Base interface for storing the results of a single run of the experiment.
        This class is instantiated in the `Storage.Experiment.trial()` method.
        """

        def __init__(self, conn, tunables: TunableGroups, experiment_id: str, trial_id: int):
            self._conn = conn
            self._tunables = tunables
            self._experiment_id = experiment_id
            self._trial_id = trial_id

        def __repr__(self) -> str:
            return f"{self._experiment_id}:{self._trial_id}"

        @property
        def trial_id(self) -> int:
            """
            ID of the current trial.
            """
            return self._trial_id

        @property
        def tunables(self) -> TunableGroups:
            """
            Tunable parameters of the current trial.
            """
            return self._tunables

        def config(self, global_config: dict) -> dict:
            """
            Produce a copy of the global configuration updated with
            parameters of the current run.
            """
            config = global_config.copy()
            config["experimentId"] = self._experiment_id
            config["trialId"] = self._trial_id
            return config

        @abstractmethod
        def update(self, status: Status, value: dict = None):
            """
            Update the storage with the results of the experiment.
            """

        @abstractmethod
        def update_telemetry(self, status: Status, value: dict = None):
            """
            Save the experiment's telemetry data and intermediate status.
            """
