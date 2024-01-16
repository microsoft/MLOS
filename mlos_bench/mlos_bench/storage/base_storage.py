#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base interface for saving and restoring the benchmark data.
"""

import logging
from abc import ABCMeta, abstractmethod
from datetime import datetime
from types import TracebackType
from typing import Optional, Union, List, Tuple, Dict, Iterator, Type, Any
from typing_extensions import Literal

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import get_git_info

_LOG = logging.getLogger(__name__)


class Storage(metaclass=ABCMeta):
    """
    An abstract interface between the benchmarking framework
    and storage systems (e.g., SQLite or MLFLow).
    """

    def __init__(self,
                 tunables: TunableGroups,
                 config: Dict[str, Any],
                 global_config: Optional[dict] = None,
                 service: Optional[Service] = None):
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
        self._validate_json_config(config)
        self._tunables = tunables.copy()
        self._service = service
        self._config = config.copy()
        self._global_config = global_config or {}

    def _validate_json_config(self, config: dict) -> None:
        """
        Reconstructs a basic json config that this class might have been
        instantiated from in order to validate configs provided outside the
        file loading mechanism.
        """
        json_config: dict = {
            "class": self.__class__.__module__ + "." + self.__class__.__name__,
        }
        if config:
            json_config["config"] = config
        ConfigSchema.STORAGE.validate(json_config)

    @property
    @abstractmethod
    def experiments(self) -> Dict[str, ExperimentData]:
        """
        Retrieve the experiments' data from the storage.

        Returns
        -------
        experiments : Dict[str, ExperimentData]
            A dictionary of the experiments' data, keyed by experiment id.
        """

    @abstractmethod
    def experiment(self, *,
                   experiment_id: str,
                   trial_id: int,
                   root_env_config: str,
                   description: str,
                   opt_target: str,
                   opt_direction: Optional[str]) -> 'Storage.Experiment':
        """
        Create a new experiment in the storage.

        We need the `opt_target` parameter here to know what metric to retrieve
        when we load the data from previous trials. Later we will replace it with
        full metadata about the optimization direction, multiple objectives, etc.

        Parameters
        ----------
        experiment_id : str
            Unique identifier of the experiment.
        trial_id : int
            Starting number of the trial.
        root_env_config : str
            A path to the root JSON configuration file of the benchmarking environment.
        description : str
            Human-readable description of the experiment.
        opt_target : str
            Name of metric we're optimizing for.
        opt_direction: Optional[str]
            Direction to optimize the metric (e.g., min or max)

        Returns
        -------
        experiment : Storage.Experiment
            An object that allows to update the storage with
            the results of the experiment and related data.
        """

    class Experiment(metaclass=ABCMeta):
        # pylint: disable=too-many-instance-attributes
        """
        Base interface for storing the results of the experiment.
        This class is instantiated in the `Storage.experiment()` method.
        """

        def __init__(self,
                     *,
                     tunables: TunableGroups,
                     experiment_id: str,
                     trial_id: int,
                     root_env_config: str,
                     description: str,
                     opt_target: str,
                     opt_direction: Optional[str]):
            self._tunables = tunables.copy()
            self._trial_id = trial_id
            self._experiment_id = experiment_id
            (self._git_repo, self._git_commit, self._root_env_config) = get_git_info(root_env_config)
            self._description = description
            self._opt_target = opt_target
            assert opt_direction in {None, "min", "max"}
            self._opt_direction = opt_direction

        def __enter__(self) -> 'Storage.Experiment':
            """
            Enter the context of the experiment.

            Override the `_setup` method to add custom context initialization.
            """
            _LOG.debug("Starting experiment: %s", self)
            self._setup()
            return self

        def __exit__(self, exc_type: Optional[Type[BaseException]],
                     exc_val: Optional[BaseException],
                     exc_tb: Optional[TracebackType]) -> Literal[False]:
            """
            End the context of the experiment.

            Override the `_teardown` method to add custom context teardown logic.
            """
            is_ok = exc_val is None
            if is_ok:
                _LOG.debug("Finishing experiment: %s", self)
            else:
                assert exc_type and exc_val
                _LOG.warning("Finishing experiment: %s", self,
                             exc_info=(exc_type, exc_val, exc_tb))
            self._teardown(is_ok)
            return False  # Do not suppress exceptions

        def __repr__(self) -> str:
            return self._experiment_id

        def _setup(self) -> None:
            """
            Create a record of the new experiment or find an existing one in the storage.

            This method is called by `Storage.Experiment.__enter__()`.
            """

        def _teardown(self, is_ok: bool) -> None:
            """
            Finalize the experiment in the storage.

            This method is called by `Storage.Experiment.__exit__()`.

            Parameters
            ----------
            is_ok : bool
                True if there were no exceptions during the experiment, False otherwise.
            """

        @property
        def experiment_id(self) -> str:
            """Get the Experiment's ID"""
            return self._experiment_id

        @property
        def trial_id(self) -> int:
            """Get the current Trial ID"""
            return self._trial_id

        @property
        def description(self) -> str:
            """Get the Experiment's description"""
            return self._description

        @property
        def opt_target(self) -> str:
            """Get the Experiment's optimization target"""
            return self._opt_target

        @property
        def opt_direction(self) -> Optional[str]:
            """Get the Experiment's optimization target"""
            return self._opt_direction

        @abstractmethod
        def merge(self, experiment_ids: List[str]) -> None:
            """
            Merge in the results of other (compatible) experiments trials.
            Used to help warm up the optimizer for this experiment.

            Parameters
            ----------
            experiment_ids : List[str]
                List of IDs of the experiments to merge in.
            """

        @abstractmethod
        def load_tunable_config(self, config_id: int) -> Dict[str, Any]:
            """
            Load tunable values for a given config ID.
            """

        @abstractmethod
        def load_telemetry(self, trial_id: int) -> List[Tuple[datetime, str, Any]]:
            """
            Retrieve the telemetry data for a given trial.

            Parameters
            ----------
            trial_id : int
                Trial ID.

            Returns
            -------
            metrics : List[Tuple[datetime, str, Any]]
                Telemetry data.
            """

        @abstractmethod
        def load(self, opt_target: Optional[str] = None) -> Tuple[List[dict], List[Optional[float]], List[Status]]:
            """
            Load (tunable values, benchmark scores, status) to warm-up the optimizer.
            This call returns data from ALL merged-in experiments and attempts
            to impute the missing tunable values.
            """

        @abstractmethod
        def pending_trials(self) -> Iterator['Storage.Trial']:
            """
            Return an iterator over the pending trial runs for this experiment.
            """

        @abstractmethod
        def new_trial(self, tunables: TunableGroups,
                      config: Optional[Dict[str, Any]] = None) -> 'Storage.Trial':
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
                the results of the experiment trial run.
            """

    class Trial(metaclass=ABCMeta):
        # pylint: disable=too-many-instance-attributes
        """
        Base interface for storing the results of a single run of the experiment.
        This class is instantiated in the `Storage.Experiment.trial()` method.
        """

        def __init__(self, *,
                     tunables: TunableGroups, experiment_id: str, trial_id: int,
                     config_id: int, opt_target: str, opt_direction: Optional[str],
                     config: Optional[Dict[str, Any]] = None):
            self._tunables = tunables
            self._experiment_id = experiment_id
            self._trial_id = trial_id
            self._config_id = config_id
            self._opt_target = opt_target
            assert opt_direction in {None, "min", "max"}
            self._opt_direction = opt_direction
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
        def config_id(self) -> int:
            """
            ID of the current trial configuration.
            """
            return self._config_id

        @property
        def opt_target(self) -> str:
            """
            Get the Trial's optimization target.
            """
            return self._opt_target

        @property
        def opt_direction(self) -> Optional[str]:
            """
            Get the Trial's optimization direction (e.g., min or max)
            """
            return self._opt_direction

        @property
        def tunables(self) -> TunableGroups:
            """
            Tunable parameters of the current trial

            (e.g., application Environment's "config")
            """
            return self._tunables

        def config(self, global_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """
            Produce a copy of the global configuration updated
            with the parameters of the current trial.

            Note: this is not the target Environment's "config" (i.e., tunable
            params), but rather the internal "config" which consists of a
            combination of somewhat more static variables defined in the json config
            files.
            """
            config = self._config.copy()
            config.update(global_config or {})
            config["experiment_id"] = self._experiment_id
            config["trial_id"] = self._trial_id
            return config

        @abstractmethod
        def update(self, status: Status, timestamp: datetime,
                   metrics: Optional[Union[Dict[str, Any], float]] = None
                   ) -> Optional[Dict[str, Any]]:
            """
            Update the storage with the results of the experiment.

            Parameters
            ----------
            status : Status
                Status of the experiment run.
            timestamp: datetime
                Timestamp of the status and metrics.
            metrics : Optional[Union[Dict[str, Any], float]]
                One or several metrics of the experiment run.
                Must contain the (float) optimization target if the status is SUCCEEDED.

            Returns
            -------
            metrics : Optional[Dict[str, Any]]
                Same as `metrics`, but always in the dict format.
            """
            _LOG.info("Store trial: %s :: %s %s", self, status, metrics)
            if isinstance(metrics, dict) and self._opt_target not in metrics:
                _LOG.warning("Trial %s :: opt.target missing: %s", self, self._opt_target)
                # raise ValueError(
                #     f"Optimization target '{self._opt_target}' is missing from {metrics}")
            return {self._opt_target: metrics} if isinstance(metrics, (float, int)) else metrics

        @abstractmethod
        def update_telemetry(self, status: Status,
                             metrics: List[Tuple[datetime, str, Any]]) -> None:
            """
            Save the experiment's telemetry data and intermediate status.

            Parameters
            ----------
            status : Status
                Current status of the trial.
            metrics : List[Tuple[datetime, str, Any]]
                Telemetry data.
            """
            _LOG.info("Store telemetry: %s :: %s %d records", self, status, len(metrics))
