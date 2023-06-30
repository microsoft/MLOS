#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base interface for saving and restoring the benchmark data.
"""

import logging
from abc import ABCMeta, abstractmethod

from types import TracebackType
from typing import Optional, Union, List, Tuple, Dict, Iterator, Type, Any
from typing_extensions import Literal

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import get_git_info

_LOG = logging.getLogger(__name__)


class Storage(metaclass=ABCMeta):
    # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """
    An abstract interface between the benchmarking framework
    and storage systems (e.g., SQLite or MLFLow).
    """

    def __init__(self, tunables: TunableGroups, service: Optional[Service],
                 config: Dict[str, Any]):
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
    def experiment(self, *,
                   experiment_id: str,
                   trial_id: int,
                   root_env_config: str,
                   description: str,
                   opt_target: str) -> 'Storage.Experiment':
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

        def __init__(self, tunables: TunableGroups, experiment_id: str, root_env_config: str):
            self._tunables = tunables.copy()
            self._experiment_id = experiment_id
            (self._git_repo, self._git_commit, self._root_env_config) = get_git_info(root_env_config)

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
        """
        Base interface for storing the results of a single run of the experiment.
        This class is instantiated in the `Storage.Experiment.trial()` method.
        """

        def __init__(self, *,
                     tunables: TunableGroups, experiment_id: str, trial_id: int,
                     config_id: int, opt_target: str, config: Optional[Dict[str, Any]] = None):
            self._tunables = tunables
            self._experiment_id = experiment_id
            self._trial_id = trial_id
            self._config_id = config_id
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
        def config_id(self) -> int:
            """
            ID of the current trial configuration.
            """
            return self._config_id

        @property
        def tunables(self) -> TunableGroups:
            """
            Tunable parameters of the current trial.
            """
            return self._tunables

        def config(self, global_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
                   metrics: Optional[Union[Dict[str, float], float]] = None
                   ) -> Optional[Dict[str, float]]:
            """
            Update the storage with the results of the experiment.

            Parameters
            ----------
            status : Status
                Status of the experiment run.
            metrics : Optional[Union[Dict[str, float], float]]
                One or several metrics of the experiment run.
                Must contain the optimization target if the status is SUCCEEDED.

            Returns
            -------
            metrics : Optional[Dict[str, float]]
                Same as `metrics`, but always in the dict format.
            """
            _LOG.info("Store trial: %s :: %s %s", self, status, metrics)
            if isinstance(metrics, dict) and self._opt_target not in metrics:
                _LOG.warning("Trial %s :: opt. target missing: %s", self, self._opt_target)
                # raise ValueError(
                #     f"Optimization target '{self._opt_target}' is missing from {metrics}")
            return {self._opt_target: metrics} if isinstance(metrics, (float, int)) else metrics

        @abstractmethod
        def update_telemetry(self, status: Status,
                             metrics: Optional[Dict[str, float]] = None) -> None:
            """
            Save the experiment's telemetry data and intermediate status.

            Parameters
            ----------
            status : Status
                Current status of the trial.
            metrics : Optional[Dict[str, float]]
                Telemetry data.
            """
            _LOG.info("Store telemetry: %s :: %s %s", self, status, metrics)
