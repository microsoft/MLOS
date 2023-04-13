#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base interface for saving and restoring the benchmark data.
"""

import logging
from abc import ABCMeta, abstractmethod
from typing import Optional, Union, List, Tuple, Dict, Any

from mlos_bench.environment import Status
from mlos_bench.service import Service
from mlos_bench.tunables import TunableGroups
from mlos_bench.util import get_git_info

_LOG = logging.getLogger(__name__)

# pylint: disable=too-few-public-methods,too-many-arguments


class Storage(metaclass=ABCMeta):
    """
    An abstract interface between the benchmarking framework
    and storage systems (e.g., SQLite or MLFLow).
    """

    def __init__(self, tunables: TunableGroups, service: Optional[Service], config: dict):
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

    @abstractmethod
    def experiment(self, exp_id: str, trial_id: int, description: str, opt_target: str):
        """
        Create a new experiment in the storage.

        Parameters
        ----------
        exp_id : str
            Unique identifier of the experiment.
        trial_id : int
            Starting number of the trial.
        description : str
            Human-readable description of the experiment.
        opt_target : str
            Name of metric we're optimizing for.

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

        def __init__(self, tunables: TunableGroups, experiment_id: str,
                     trial_id: int, description: str, opt_target: str):
            self._tunables = tunables  # No need to copy, it's immutable
            self._experiment_id = experiment_id
            self._trial_id = trial_id
            self._description = description
            self._opt_target = opt_target
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
        def load(self, opt_target: Optional[str] = None) -> Tuple[List[dict], List[float]]:
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
        def trial(self, tunables: TunableGroups, config: Optional[Dict[str, Any]] = None):
            """
            Create a new experiment run in the storage.

            Parameters
            ----------
            tunables : TunableGroups
                Tunable parameters of the experiment.
            config : dict
                Key/value pairs of additional non-tunable parameters of the trial.

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

        def __init__(self, engine, tunables: TunableGroups, experiment_id: str,
                     trial_id: int, opt_target: str, config: Optional[Dict[str, Any]] = None):
            self._engine = engine
            self._tunables = tunables
            self._experiment_id = experiment_id
            self._trial_id = trial_id
            self._opt_target = opt_target
            self._config = config or {}

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

        def config(self, global_config: Optional[Dict[str, Any]] = None) -> dict:
            """
            Produce a copy of the global configuration updated
            with the parameters of the current trial.
            """
            config = self._config.copy()
            config.update(global_config or {})
            config["experimentId"] = self._experiment_id
            config["trialId"] = self._trial_id
            return config

        @abstractmethod
        def update(self, status: Status,
                   value: Optional[Union[Dict[str, Any], Any]] = None
                   ) -> Optional[Dict[str, Any]]:
            """
            Update the storage with the results of the experiment.

            Parameters
            ----------
            status : Status
                Status of the experiment run.
            value : Optional[Union[Dict[str, float], float]]
                One or several metrics of the experiment run.
                Must contain the optimization target if the status is SUCCEEDED.

            Returns
            -------
            value : Optional[Dict[str, float]]
                Same as value, but always in the dict format.
            """
            _LOG.info("Store trial: %s :: %s %s", self, status, value)
            if isinstance(value, dict) and self._opt_target not in value:
                _LOG.warning("Trial %s :: opt. target missing: %s", self, self._opt_target)
                # raise ValueError(
                #     f"Optimization target '{self._opt_target}' is missing from {value}")
            return {self._opt_target: value} if isinstance(value, (float, int)) else value

        @abstractmethod
        def update_telemetry(self, status: Status, value: Optional[Dict[str, Any]] = None):
            """
            Save the experiment's telemetry data and intermediate status.

            Parameters
            ----------
            status : Status
                Current status of the trial.
            value : Optional[Dict[str, float]]
                Telemetry data.
            """
            _LOG.info("Store telemetry: %s :: %s %s", self, status, value)
