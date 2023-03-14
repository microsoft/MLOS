"""
Base interface for saving and restoring the benchmark data.
"""

import logging
from abc import ABCMeta, abstractmethod
from typing import List

import pandas

from mlos_bench.environment import Status
from mlos_bench.tunables import TunableGroups
from mlos_bench.util import prepare_class_load, instantiate_from_config

_LOG = logging.getLogger(__name__)


class Storage(metaclass=ABCMeta):
    """
    An abstract interface between the benchmarking framework
    and storage systems (e.g., SQLite or MLFLow).
    """

    @staticmethod
    def load(config: dict, global_config: dict = None):
        """
        Instantiate the Storage object from configuration.

        Parameters
        ----------
        config : dict
            Configuration of the storage system, as loaded from JSON.
        global_config : dict
            Global configuration parameters (optional).

        Returns
        -------
        db : Storage
            A new instance of the Storage class.
        """
        (class_name, db_config) = prepare_class_load(config, global_config)
        storage = Storage.new(class_name, db_config)
        _LOG.info("Created storage: %s", storage)
        return storage

    @classmethod
    def new(cls, class_name: str, config: dict):
        """
        Factory method for a new Storage object with a given config.

        Parameters
        ----------
        class_name: str
            FQN of a Python class to instantiate.
            Must be derived from the `Storage` class.
        config : dict
            Free-format dictionary that contains the storage configuration.
            It will be passed as a constructor parameter of the class
            specified by `class_name`.

        Returns
        -------
        db : Optimizer
            An instance of the `Storage` class initialized with `config`.
        """
        return instantiate_from_config(cls, class_name, config)

    def __init__(self, config: dict):
        """
        Create a new storage object.

        Parameters
        ----------
        config : dict
            Free-format key/value pairs of configuration parameters.
        """
        _LOG.debug("Storage config: %s", config)
        self._config = config.copy()
        self._experiment_id = self._config["experimentId"]
        self._run_id = self._config.get("runId")
        if self._run_id is not None:
            self._run_id = int(self._run_id)

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

        def __init__(self, storage, experiment_id: str):
            self._storage = storage
            self._experiment_id = experiment_id

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
        def load(self) -> pandas.DataFrame:
            """
            Load (tunable values, status, value) to warm-up the optimizer.
            This call returns data from ALL merged-in experiments and attempts
            to impute the missing tunable values.
            """

        @abstractmethod
        def pending(self):
            """
            Return an iterator over the pending experiment runs.
            """

        @abstractmethod
        def run(self, tunables: TunableGroups):
            """
            Create a new experiment run in the storage.

            Parameters
            ----------
            tunables : TunableGroups
                Tunable parameters of the experiment.

            Returns
            -------
            run : Storage.Run
                An object that allows to update the storage with
                the results of the experiment run.
            """

    class Run(metaclass=ABCMeta):
        """
        Base interface for storing the results of a single run of the experiment.
        This class is instantiated in the `Storage.Experiment.run()` method.
        """

        def __init__(self, storage, tunables: TunableGroups, experiment_id: str, run_id: int):
            self._storage = storage
            self._tunables = tunables
            self._experiment_id = experiment_id
            self._run_id = run_id

        def __enter__(self):
            """
            Enter the context of the experiment run.
            """
            _LOG.debug("Starting experiment run: %s", self)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            """
            End the context of the experiment run.
            """
            if exc_val is None:
                _LOG.debug("Finishing experiment run: %s", self)
            else:
                _LOG.warning("Finishing experiment run: %s",
                             self, exc_info=(exc_type, exc_val, exc_tb))
            return False  # Do not suppress exceptions

        def __repr__(self) -> str:
            return f"{self._experiment_id}:{self._run_id}"

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
            config["runId"] = self._run_id
            return config

        @abstractmethod
        def update(self, status: Status, value: pandas.DataFrame = None):
            """
            Update the storage with the results of the experiment.
            """
