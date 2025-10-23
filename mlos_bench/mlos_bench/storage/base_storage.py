#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base interface for saving and restoring the benchmark data.

See Also
--------
mlos_bench.storage.base_storage.Storage.experiments :
    Retrieves a dictionary of the Experiments' data.
mlos_bench.storage.base_experiment_data.ExperimentData.results_df :
    Retrieves a pandas DataFrame of the Experiment's trials' results data.
mlos_bench.storage.base_experiment_data.ExperimentData.trials :
    Retrieves a dictionary of the Experiment's trials' data.
mlos_bench.storage.base_experiment_data.ExperimentData.tunable_configs :
    Retrieves a dictionary of the Experiment's sampled configs data.
mlos_bench.storage.base_experiment_data.ExperimentData.tunable_config_trial_groups :
    Retrieves a dictionary of the Experiment's trials' data, grouped by shared
    tunable config.
mlos_bench.storage.base_trial_data.TrialData :
    Base interface for accessing the stored benchmark trial data.
"""

from __future__ import annotations

import logging
from abc import ABCMeta, abstractmethod
from collections.abc import Iterator, Mapping
from contextlib import AbstractContextManager as ContextManager
from datetime import datetime
from subprocess import CalledProcessError
from types import TracebackType
from typing import Any, Literal

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.dict_templater import DictTemplater
from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import get_git_info

_LOG = logging.getLogger(__name__)


class Storage(metaclass=ABCMeta):
    """An abstract interface between the benchmarking framework and storage systems
    (e.g., SQLite or MLFLow).
    """

    def __init__(
        self,
        config: dict[str, Any],
        global_config: dict | None = None,
        service: Service | None = None,
    ):
        """
        Create a new storage object.

        Parameters
        ----------
        config : dict
            Free-format key/value pairs of configuration parameters.
        """
        _LOG.debug("Storage config: %s", config)
        self._validate_json_config(config)
        self._service = service
        self._config = config.copy()
        self._global_config = global_config or {}

    @abstractmethod
    def update_schema(self) -> None:
        """Update the schema of the storage backend if needed."""

    def _validate_json_config(self, config: dict) -> None:
        """Reconstructs a basic json config that this class might have been instantiated
        from in order to validate configs provided outside the file loading
        mechanism.
        """
        json_config: dict = {
            "class": self.__class__.__module__ + "." + self.__class__.__name__,
        }
        if config:
            json_config["config"] = config
        ConfigSchema.STORAGE.validate(json_config)

    @property
    @abstractmethod
    def experiments(self) -> dict[str, ExperimentData]:
        """
        Retrieve the experiments' data from the storage.

        Returns
        -------
        experiments : dict[str, ExperimentData]
            A dictionary of the experiments' data, keyed by experiment id.
        """

    @abstractmethod
    def get_experiment_by_id(
        self,
        experiment_id: str,
        tunables: TunableGroups,
        opt_targets: dict[str, Literal["min", "max"]],
    ) -> Storage.Experiment | None:
        """
        Gets an Experiment by its ID.

        Parameters
        ----------
        experiment_id : str
            ID of the Experiment to retrieve.
        tunables : TunableGroups
            The tunables for the Experiment.
        opt_targets : dict[str, Literal["min", "max"]]
            The optimization targets for the Experiment's
            :py:class:`~mlos_bench.optimizers.base_optimizer.Optimizer`.

        Returns
        -------
        experiment : Storage.Experiment | None
            The Experiment object, or None if it doesn't exist.

        Notes
        -----
        Tunables are not stored in the database for the Experiment, only for the
        Trials, so currently they can change if the user (incorrectly) adjusts
        the configs on disk between resume runs.
        Since this method is generally meant to load th Experiment from the
        database for a child process to execute a Trial in the background we are
        generally safe to simply pass these values from the parent process
        rather than look them up in the database.
        """

    @abstractmethod
    def experiment(  # pylint: disable=too-many-arguments
        self,
        *,
        experiment_id: str,
        trial_id: int,
        root_env_config: str,
        description: str,
        tunables: TunableGroups,
        opt_targets: dict[str, Literal["min", "max"]],
    ) -> Storage.Experiment:
        """
        Create or reload an experiment in the Storage.

        Notes
        -----
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
        tunables : TunableGroups
        opt_targets : dict[str, Literal["min", "max"]]
            Names of metrics we're optimizing for and the optimization direction {min, max}.

        Returns
        -------
        experiment : Storage.Experiment
            An object that allows to update the storage with
            the results of the experiment and related data.
        """

    class Experiment(ContextManager, metaclass=ABCMeta):
        # pylint: disable=too-many-instance-attributes
        """
        Base interface for storing the results of the experiment.

        This class is instantiated in the `Storage.experiment()` method.
        """

        def __init__(  # pylint: disable=too-many-arguments
            self,
            *,
            tunables: TunableGroups,
            experiment_id: str,
            trial_id: int,
            root_env_config: str | None,
            description: str,
            opt_targets: dict[str, Literal["min", "max"]],
            git_repo: str | None = None,
            git_commit: str | None = None,
            git_rel_root_env_config: str | None = None,
        ):
            self._tunables = tunables.copy()
            self._trial_id = trial_id
            self._experiment_id = experiment_id
            self._abs_root_env_config: str | None
            if root_env_config is not None:
                if git_repo or git_commit or git_rel_root_env_config:
                    # Extra args are only used when restoring an Experiment from the DB.
                    raise ValueError("Unexpected args: git_repo, git_commit, rel_root_env_config")
                try:
                    (
                        self._git_repo,
                        self._git_commit,
                        self._git_rel_root_env_config,
                        self._abs_root_env_config,
                    ) = get_git_info(root_env_config)
                except CalledProcessError as e:
                    # Note: currently the Experiment schema requires git
                    # metadata to be set.  We *could* set the git metadata to
                    # dummy values, but for now we just throw an error.
                    _LOG.warning(
                        "Failed to get git info for root_env_config %s: %s",
                        root_env_config,
                        e,
                    )
                    raise e
            else:
                # Restoring from DB.
                if not (git_repo and git_commit and git_rel_root_env_config):
                    raise ValueError("Missing args: git_repo, git_commit, rel_root_env_config")
                self._git_repo = git_repo
                self._git_commit = git_commit
                self._git_rel_root_env_config = git_rel_root_env_config
                # Note: The absolute path to the root config is not stored in the DB,
                # and resolving it is not always possible, so we omit this
                # operation by default for now.
                # See commit 0cb5948865662776e92ceaca3f0a80a34c6a39ef in
                # <https://github.com/microsoft/MLOS/pull/985> for prior
                # implementation attempts.
                self._abs_root_env_config = None
            assert isinstance(
                self._git_rel_root_env_config, str
            ), "Failed to get relative root config path"
            _LOG.info(
                "Resolved relative root_config %s from %s at commit %s for Experiment %s to %s",
                self._git_rel_root_env_config,
                self._git_repo,
                self._git_commit,
                self._experiment_id,
                self._abs_root_env_config,
            )
            self._description = description
            self._opt_targets = opt_targets
            self._in_context = False

        def __enter__(self) -> Storage.Experiment:
            """
            Enter the context of the experiment.

            Notes
            -----
            Override the `_setup` method to add custom context initialization.
            """
            _LOG.debug("Starting experiment: %s", self)
            assert not self._in_context
            self._setup()
            self._in_context = True
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
        ) -> Literal[False]:
            """
            End the context of the experiment.

            Notes
            -----
            Override the `_teardown` method to add custom context teardown logic.
            """
            is_ok = exc_val is None
            if is_ok:
                _LOG.debug("Finishing experiment: %s", self)
            else:
                assert exc_type and exc_val
                _LOG.warning(
                    "Finishing experiment: %s",
                    self,
                    exc_info=(exc_type, exc_val, exc_tb),
                )
            assert self._in_context
            self._teardown(is_ok)
            self._in_context = False
            return False  # Do not suppress exceptions

        def __repr__(self) -> str:
            return self._experiment_id

        def _setup(self) -> None:
            """
            Create a record of the new experiment or find an existing one in the
            storage.

            This method is called by :py:class:`.Storage.Experiment.__enter__()`.
            """

        def _teardown(self, is_ok: bool) -> None:
            """
            Finalize the experiment in the storage.

            This method is called by :py:class:`.Storage.Experiment.__exit__()`.

            Parameters
            ----------
            is_ok : bool
                True if there were no exceptions during the experiment, False otherwise.
            """

        @property
        def experiment_id(self) -> str:
            """Get the Experiment's ID."""
            return self._experiment_id

        @property
        def trial_id(self) -> int:
            """Get the current Trial ID."""
            return self._trial_id

        @property
        def description(self) -> str:
            """Get the Experiment's description."""
            return self._description

        @property
        def rel_root_env_config(self) -> str:
            """Get the Experiment's root Environment config's relative file path to the
            git repo root.
            """
            return self._git_rel_root_env_config

        @property
        def abs_root_env_config(self) -> str | None:
            """
            Get the Experiment's root Environment config absolute file path.

            This attempts to return the current absolute path to the root config
            for this process instead of the path relative to the git repo root.

            However, this may not always be possible if the git repo root is not
            accessible, which can happen if the Experiment was restored from the
            DB, but the process was started from a different working directory,
            for instance.

            Notes
            -----
            This is mostly useful for other components (e.g.,
            :py:class:`~mlos_bench.schedulers.base_scheduler.Scheduler`) to use
            within the same process, and not across invocations.
            """
            # TODO: In the future, we can consider fetching the git_repo to a
            # standard working directory for ``mlos_bench`` and then resolving
            # the root config path from there based on the relative path.
            return self._abs_root_env_config

        @property
        def tunables(self) -> TunableGroups:
            """Get the Experiment's tunables."""
            return self._tunables

        @property
        def opt_targets(self) -> dict[str, Literal["min", "max"]]:
            """Get the Experiment's optimization targets and directions."""
            return self._opt_targets

        @abstractmethod
        def merge(self, experiment_ids: list[str]) -> None:
            """
            Merge in the results of other (compatible) experiments trials. Used to help
            warm up the optimizer for this experiment.

            Parameters
            ----------
            experiment_ids : list[str]
                List of IDs of the experiments to merge in.
            """

        @abstractmethod
        def load_tunable_config(self, config_id: int) -> dict[str, Any]:
            """Load tunable values for a given config ID."""

        @abstractmethod
        def load_telemetry(self, trial_id: int) -> list[tuple[datetime, str, Any]]:
            """
            Retrieve the telemetry data for a given trial.

            Parameters
            ----------
            trial_id : int
                Trial ID.

            Returns
            -------
            metrics : list[tuple[datetime.datetime, str, Any]]
                Telemetry data.
            """

        @abstractmethod
        def load(
            self,
            last_trial_id: int = -1,
        ) -> tuple[list[int], list[dict], list[dict[str, Any] | None], list[Status]]:
            """
            Load (tunable values, benchmark scores, status) to warm-up the optimizer.

            If `last_trial_id` is present, load only the data from the (completed) trials
            that were scheduled *after* the given trial ID. Otherwise, return data from ALL
            merged-in experiments and attempt to impute the missing tunable values.

            Parameters
            ----------
            last_trial_id : int
                (Optional) Trial ID to start from.

            Returns
            -------
            (trial_ids, configs, scores, status) : ([int], [dict], [dict] | None, [Status])
                Trial ids, Tunable values, benchmark scores, and status of the trials.
            """

        @abstractmethod
        def get_trial_by_id(
            self,
            trial_id: int,
        ) -> Storage.Trial | None:
            """
            Gets a Trial by its ID.

            Parameters
            ----------
            trial_id : int
                ID of the Trial to retrieve for this Experiment.

            Returns
            -------
            trial : Storage.Trial | None
                The Trial object, or None if it doesn't exist.
            """

        @abstractmethod
        def pending_trials(
            self,
            timestamp: datetime,
            *,
            running: bool,
            trial_runner_assigned: bool | None = None,
        ) -> Iterator[Storage.Trial]:
            """
            Return an iterator over :py:attr:`~.Status.PENDING`
            :py:class:`~.Storage.Trial` instances that have a scheduled start time to
            run on or before the specified timestamp.

            Parameters
            ----------
            timestamp : datetime.datetime
                The time in UTC to check for scheduled Trials.
            running : bool
                If True, include the Trials that are also
                :py:attr:`~.Status.RUNNING` or :py:attr:`~.Status.READY`.
                Otherwise, return only the scheduled trials.
            trial_runner_assigned : bool | None
                If True, include the Trials that are assigned to a
                :py:class:`~.TrialRunner`. If False, return only the trials
                that are not assigned to any :py:class:`~.TrialRunner`.
                If None, return all trials regardless of their assignment.

            Returns
            -------
            trials : Iterator[Storage.Trial]
                An iterator over the scheduled (and maybe running) trials.
            """

        def new_trial(
            self,
            tunables: TunableGroups,
            ts_start: datetime | None = None,
            config: dict[str, Any] | None = None,
        ) -> Storage.Trial:
            """
            Create a new experiment run in the storage.

            Parameters
            ----------
            tunables : TunableGroups
                Tunable parameters to use for the trial.
            ts_start : datetime.datetime | None
                Timestamp of the trial start (can be in the future).
            config : dict
                Key/value pairs of additional non-tunable parameters of the trial.

            Returns
            -------
            trial : Storage.Trial
                An object that allows to update the storage with
                the results of the experiment trial run.
            """
            # Check that `config` is json serializable (e.g., no callables)
            if config:
                try:
                    # Relies on the fact that DictTemplater only accepts primitive
                    # types in it's nested dict structure walk.
                    _config = DictTemplater(config).expand_vars()
                    assert isinstance(_config, dict)
                except ValueError as e:
                    _LOG.error("Non-serializable config: %s", config, exc_info=e)
                    raise e
            return self._new_trial(tunables, ts_start, config)

        @abstractmethod
        def _new_trial(
            self,
            tunables: TunableGroups,
            ts_start: datetime | None = None,
            config: dict[str, Any] | None = None,
        ) -> Storage.Trial:
            """
            Create a new experiment run in the storage.

            Parameters
            ----------
            tunables : TunableGroups
                Tunable parameters to use for the trial.
            ts_start : datetime.datetime | None
                Timestamp of the trial start (can be in the future).
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

        def __init__(  # pylint: disable=too-many-arguments
            self,
            *,
            tunables: TunableGroups,
            experiment_id: str,
            trial_id: int,
            tunable_config_id: int,
            trial_runner_id: int | None,
            opt_targets: dict[str, Literal["min", "max"]],
            status: Status,
            restoring: bool,
            config: dict[str, Any] | None = None,
        ):
            if not restoring and status not in (Status.UNKNOWN, Status.PENDING):
                raise ValueError(f"Invalid status for a new trial: {status}")
            self._tunables = tunables
            self._experiment_id = experiment_id
            self._trial_id = trial_id
            self._tunable_config_id = tunable_config_id
            self._trial_runner_id = trial_runner_id
            self._opt_targets = opt_targets
            self._config = config or {}
            self._status = status

        def __repr__(self) -> str:
            return (
                f"{self._experiment_id}:{self._trial_id}:"
                f"{self._tunable_config_id}:{self.trial_runner_id}"
            )

        @property
        def experiment_id(self) -> str:
            """Experiment ID of the Trial."""
            return self._experiment_id

        @property
        def trial_id(self) -> int:
            """ID of the current trial."""
            return self._trial_id

        @property
        def tunable_config_id(self) -> int:
            """ID of the current trial (tunable) configuration."""
            return self._tunable_config_id

        @property
        def trial_runner_id(self) -> int | None:
            """ID of the TrialRunner this trial is assigned to."""
            return self._trial_runner_id

        def opt_targets(self) -> dict[str, Literal["min", "max"]]:
            """Get the Trial's optimization targets and directions."""
            return self._opt_targets

        @property
        def tunables(self) -> TunableGroups:
            """
            Tunable parameters of the current trial.

            (e.g., application Environment's "config")
            """
            return self._tunables

        @abstractmethod
        def set_trial_runner(self, trial_runner_id: int) -> int:
            """Assign the trial to a specific TrialRunner."""
            if self._trial_runner_id is None or self._status.is_pending():
                _LOG.debug(
                    "%sSetting Trial %s to TrialRunner %d",
                    "Re-" if self._trial_runner_id else "",
                    self,
                    trial_runner_id,
                )
                self._trial_runner_id = trial_runner_id
            else:
                _LOG.warning(
                    "Trial %s already assigned to a TrialRunner, cannot switch to %d",
                    self,
                    self._trial_runner_id,
                )
            return self._trial_runner_id

        def config(self, global_config: dict[str, Any] | None = None) -> dict[str, Any]:
            """
            Produce a copy of the global configuration updated with the parameters of
            the current trial.

            Note: this is not the target Environment's "config" (i.e., tunable
            params), but rather the internal "config" which consists of a
            combination of somewhat more static variables defined in the json config
            files.
            """
            config = self._config.copy()
            config.update(global_config or {})
            # Here we add some built-in variables for the trial to use while it's running.
            config["experiment_id"] = self._experiment_id
            config["trial_id"] = self._trial_id
            trial_runner_id = self.trial_runner_id
            if trial_runner_id is not None:
                config["trial_runner_id"] = trial_runner_id
            return config

        def add_new_config_data(
            self,
            new_config_data: Mapping[str, int | float | str],
        ) -> None:
            """
            Add new config data to the trial.

            Parameters
            ----------
            new_config_data : dict[str, int | float | str]
                New data to add (must not already exist for the trial).

            Raises
            ------
            ValueError
                If any of the data already exists.
            """
            for key, value in new_config_data.items():
                if key in self._config:
                    raise ValueError(
                        f"New config data {key}={value} already exists for trial {self}: "
                        f"{self._config[key]}"
                    )
                self._config[key] = value
            self._save_new_config_data(new_config_data)

        @abstractmethod
        def _save_new_config_data(
            self,
            new_config_data: Mapping[str, int | float | str],
        ) -> None:
            """
            Save the new config data to the storage.

            Parameters
            ----------
            new_config_data : dict[str, int | float | str]]
                New data to add.
            """

        @property
        def status(self) -> Status:
            """Get the status of the current trial."""
            return self._status

        @abstractmethod
        def update(
            self,
            status: Status,
            timestamp: datetime,
            metrics: dict[str, Any] | None = None,
        ) -> dict[str, Any] | None:
            """
            Update the storage with the results of the experiment.

            Parameters
            ----------
            status : Status
                Status of the experiment run.
            timestamp: datetime.datetime
                Timestamp of the status and metrics.
            metrics : Optional[dict[str, Any]]
                One or several metrics of the experiment run.
                Must contain the (float) optimization target if the status is SUCCEEDED.

            Returns
            -------
            metrics : Optional[dict[str, Any]]
                Same as `metrics`, but always in the dict format.
            """
            _LOG.info("Store trial: %s :: %s %s", self, status, metrics)
            if status.is_succeeded():
                assert metrics is not None
                opt_targets = set(self._opt_targets.keys())
                if not opt_targets.issubset(metrics.keys()):
                    _LOG.warning(
                        "Trial %s :: opt.targets missing: %s",
                        self,
                        opt_targets.difference(metrics.keys()),
                    )
                    # raise ValueError()
            self._status = status
            return metrics

        @abstractmethod
        def update_telemetry(
            self,
            status: Status,
            timestamp: datetime,
            metrics: list[tuple[datetime, str, Any]],
        ) -> None:
            """
            Save the experiment's telemetry data and intermediate status.

            Parameters
            ----------
            status : Status
                Current status of the trial.
            timestamp: datetime.datetime
                Timestamp of the status (but not the metrics).
            metrics : list[tuple[datetime.datetime, str, Any]]
                Telemetry data.
            """
            _LOG.info("Store telemetry: %s :: %s %d records", self, status, len(metrics))
