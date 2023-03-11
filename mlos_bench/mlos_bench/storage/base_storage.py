"""
Base interface for saving and restoring the benchmark data.
"""

import logging
from abc import ABCMeta, abstractmethod

import pandas as pd

from mlos_bench.environment import Status, TunableGroups
from mlos_bench.util import prepare_class_load, instantiate_from_config

_LOG = logging.getLogger(__name__)


class Experiment(metaclass=ABCMeta):
    """
    Base class for
    """

    def __init__(self, tunables: TunableGroups, experiment_id: str, run_id: int):
        self._tunables = tunables
        self._experiment_id = experiment_id
        self._run_id = run_id

    @abstractmethod
    def update(self, status: Status, value: pd.DataFrame = None):
        """
        Update the storage with the results of the experiment.
        """


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
    def restore(self, experiment_id: str):
        """
        Restore the experimental data from the storage.

        Parameters
        ----------
        experiment_id : str
            Unique experiment ID.
        """

    @abstractmethod
    def experiment(self, tunables: TunableGroups,
                   experiment_id: str, run_id: int) -> Experiment:
        """
        Create a new experiment in the storage.
        """
