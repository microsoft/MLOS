"""
Base interface for saving and restoring the benchmark data.
"""

import logging
from abc import ABCMeta, abstractmethod
from typing import List

import pandas as pd

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

    @abstractmethod
    def experiment(self, experiment_id: str):
        """
        Create a new experiment in the storage.

        Parameters
        ----------
        experiment_id : str
            Unique experiment ID.

        Returns
        -------
        experiment : ExperimentStorage
            An object that allows to update the storage with
            the results of the experiment and related data.
        """


class ExperimentStorage(metaclass=ABCMeta):
    """
    Base interface for storing the results of the experiment.
    This class is instantiated in the `Storage.experiment()` method.
    """

    def __init__(self, storage: Storage, experiment_id: str,):
        self._storage = storage
        self._experiment_id = experiment_id

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
    def load(self, opt_target: str = 'score', opt_is_min: bool = True):
        """
        Load (tunable values, status, value) to warm-up the optimizer.
        This call returns data from ALL merged-in experiments and attempts
        to impute the missing tunable values.

        Parameters
        ----------
        opt_target : str
            Name of the optimization target.
        opt_is_min : bool
            Whether the optimization target is a minimization problem.
        """

    @property
    @abstractmethod
    def last_run_id(self) -> int:
        """
        Return the ID of the last run in the experiment.
        """

    @abstractmethod
    def run(self, tunables: TunableGroups, run_id: int):
        """
        Create a new experiment run in the storage.

        Parameters
        ----------
        tunables : TunableGroups
            Tunable parameters of the experiment.
        run_id : int
            Unique experiment run ID.

        Returns
        -------
        run : RunStorage
            An object that allows to update the storage with
            the results of the experiment run.
        """


class RunStorage(metaclass=ABCMeta):
    """
    Base interface for storing the results of a single run of the experiment.
    This class is instantiated in the `ExperimentStorage.run()` method.
    """

    def __init__(self, storage: Storage, tunables: TunableGroups,
                 experiment_id: str, run_id: int):
        self._storage = storage
        self._tunables = tunables
        self._experiment_id = experiment_id
        self._run_id = run_id

    @abstractmethod
    def update(self, status: Status, value: pd.DataFrame = None):
        """
        Update the storage with the results of the experiment.
        """
