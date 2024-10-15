#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Base class for the optimization loop scheduling policies."""

import json
import logging
from abc import ABCMeta, abstractmethod
from datetime import datetime
from types import TracebackType
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

from pytz import UTC
from typing_extensions import Literal

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.environments.base_environment import Environment
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.schedulers.trial_runner import TrialRunner
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import merge_parameters

_LOG = logging.getLogger(__name__)


class Scheduler(metaclass=ABCMeta):
    # pylint: disable=too-many-instance-attributes
    """Base class for the optimization loop scheduling policies."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        config: Dict[str, Any],
        global_config: Dict[str, Any],
        trial_runners: List[TrialRunner],
        optimizer: Optimizer,
        storage: Storage,
        root_env_config: str,
    ):
        """
        Create a new instance of the scheduler. The constructor of this and the derived
        classes is called by the persistence service after reading the class JSON
        configuration. Other objects like the TrialRunner(s) and their Environment(s)
        and Optimizer are provided by the Launcher.

        Parameters
        ----------
        config : dict
            The configuration for the Scheduler.
        global_config : dict
            The global configuration for the experiment.
        trial_runner : List[TrialRunner]
            The set of TrialRunner(s) (and associated Environment(s)) to benchmark/optimize.
        optimizer : Optimizer
            The Optimizer to use.
        storage : Storage
            The storage to use.
        root_env_config : str
            Path to the root Environment configuration.
        """
        self.global_config = global_config
        config = merge_parameters(
            dest=config.copy(),
            source=global_config,
            required_keys=["experiment_id", "trial_id"],
        )
        self._validate_json_config(config)

        self._experiment_id = config["experiment_id"].strip()
        self._trial_id = int(config["trial_id"])
        self._config_id = int(config.get("config_id", -1))
        self._max_trials = int(config.get("max_trials", -1))
        self._trial_count = 0

        self._trial_config_repeat_count = int(config.get("trial_config_repeat_count", 1))
        if self._trial_config_repeat_count <= 0:
            raise ValueError(
                f"Invalid trial_config_repeat_count: {self._trial_config_repeat_count}"
            )

        self._do_teardown = bool(config.get("teardown", True))

        self._experiment: Optional[Storage.Experiment] = None
        self._trial_runners = trial_runners
        assert self._trial_runners, "At least one TrialRunner is required"
        self._optimizer = optimizer
        self._storage = storage
        self._root_env_config = root_env_config
        self._current_trial_runner_idx = 0
        self._last_trial_id = -1
        self._ran_trials: List[Storage.Trial] = []

        _LOG.debug("Scheduler instantiated: %s :: %s", self, config)

    def _validate_json_config(self, config: dict) -> None:
        """Reconstructs a basic json config that this class might have been instantiated
        from in order to validate configs provided outside the file loading
        mechanism.
        """
        json_config: dict = {
            "class": self.__class__.__module__ + "." + self.__class__.__name__,
        }
        if config:
            json_config["config"] = config.copy()
            # The json schema does not allow for -1 as a valid value for config_id.
            # As it is just a default placeholder value, and not required, we can
            # remove it from the config copy prior to validation safely.
            config_id = json_config["config"].get("config_id")
            if config_id is not None and isinstance(config_id, int) and config_id < 0:
                json_config["config"].pop("config_id")
        ConfigSchema.SCHEDULER.validate(json_config)

    @property
    def trial_config_repeat_count(self) -> int:
        """Gets the number of trials to run for a given config."""
        return self._trial_config_repeat_count

    @property
    def trial_count(self) -> int:
        """Gets the current number of trials run for the experiment."""
        return self._trial_count

    @property
    def max_trials(self) -> int:
        """Gets the maximum number of trials to run for a given experiment, or -1 for no
        limit.
        """
        return self._max_trials

    @property
    def experiment(self) -> Optional[Storage.Experiment]:
        """Gets the Experiment Storage."""
        return self._experiment

    @property
    def root_environment(self) -> Environment:
        """
        Gets the root (prototypical) Environment from the first TrialRunner.

        Note: All TrialRunners have the same Environment config and are made
        unique by their use of the unique trial_runner_id assigned to each
        TrialRunner's Environment's global_config.
        """
        return self._trial_runners[0].environment

    @property
    def trial_runners(self) -> List[TrialRunner]:
        """Gets the list of Trial Runners."""
        return self._trial_runners

    @property
    def environments(self) -> Iterable[Environment]:
        """Gets the Environment from the TrialRunners."""
        return (trial_runner.environment for trial_runner in self._trial_runners)

    @property
    def optimizer(self) -> Optimizer:
        """Gets the Optimizer."""
        return self._optimizer

    @property
    def storage(self) -> Storage:
        """Gets the Storage."""
        return self._storage

    def _assign_trial_runner(
        self,
        trial: Storage.Trial,
        trial_runner: Optional[TrialRunner] = None,
    ) -> TrialRunner:
        """
        Assigns a TrialRunner to the given Trial.

        The base class implements a simple round-robin scheduling algorithm.

        Subclasses can override this method to implement a more sophisticated policy.
        For instance:

        ```python
        def assign_trial_runner(
            self,
            trial: Storage.Trial,
            trial_runner: Optional[TrialRunner] = None,
        ) -> TrialRunner:
            if trial_runner is None:
                # Implement a more sophisticated policy here.
                # For example, to assign the Trial to the TrialRunner with the least
                # number of running Trials.
                # Or assign the Trial to the TrialRunner that hasn't executed this
                # TunableValues Config yet.
                trial_runner = ...
            # Call the base class method to assign the TrialRunner in the Trial's metadata.
            return super().assign_trial_runner(trial, trial_runner)
            ...
        ```

        Parameters
        ----------
        trial : Storage.Trial
            The trial to assign a TrialRunner to.
        trial_runner : Optional[TrialRunner]
            The ID of the TrialRunner to assign to the given Trial.

        Returns
        -------
        TrialRunner
            The assigned TrialRunner.
        """
        assert (
            trial.trial_runner_id is None
        ), f"Trial {trial} already has a TrialRunner assigned: {trial.trial_runner_id}"
        if trial_runner is None:
            # Basic round-robin trial runner assignment policy:
            # fetch and increment the current TrialRunner index.
            # Override in the subclass for a more sophisticated policy.
            trial_runner_id = self._current_trial_runner_idx
            self._current_trial_runner_idx += 1
            self._current_trial_runner_idx %= len(self._trial_runners)
            trial_runner = self._trial_runners[trial_runner_id]
            _LOG.info(
                "Trial %s missing trial_runner_id. Assigning %s via basic round-robin policy.",
                trial,
                trial_runner,
            )
        trial.add_new_config_data({"trial_runner_id": trial_runner.trial_runner_id})
        return trial_runner

    def get_trial_runner(self, trial: Storage.Trial) -> TrialRunner:
        """
        Gets the TrialRunner associated with the given Trial.

        Parameters
        ----------
        trial : Storage.Trial
            The trial to get the associated TrialRunner for.

        Returns
        -------
        TrialRunner
        """
        if trial.trial_runner_id is None:
            self._assign_trial_runner(trial, trial_runner=None)
        assert trial.trial_runner_id is not None
        return self._trial_runners[trial.trial_runner_id]

    def __repr__(self) -> str:
        """
        Produce a human-readable version of the Scheduler (mostly for logging).

        Returns
        -------
        string : str
            A human-readable version of the Scheduler.
        """
        return self.__class__.__name__

    def __enter__(self) -> "Scheduler":
        """Enter the scheduler's context."""
        _LOG.debug("Scheduler START :: %s", self)
        assert self.experiment is None
        self._optimizer.__enter__()
        # Start new or resume the existing experiment. Verify that the
        # experiment configuration is compatible with the previous runs.
        # If the `merge` config parameter is present, merge in the data
        # from other experiments and check for compatibility.
        self._experiment = self.storage.experiment(
            experiment_id=self._experiment_id,
            trial_id=self._trial_id,
            root_env_config=self._root_env_config,
            description=self.root_environment.name,
            tunables=self.root_environment.tunable_params,
            opt_targets=self.optimizer.targets,
        ).__enter__()
        return self

    def __exit__(
        self,
        ex_type: Optional[Type[BaseException]],
        ex_val: Optional[BaseException],
        ex_tb: Optional[TracebackType],
    ) -> Literal[False]:
        """Exit the context of the scheduler."""
        if ex_val is None:
            _LOG.debug("Scheduler END :: %s", self)
        else:
            assert ex_type and ex_val
            _LOG.warning("Scheduler END :: %s", self, exc_info=(ex_type, ex_val, ex_tb))
        assert self._experiment is not None
        self._experiment.__exit__(ex_type, ex_val, ex_tb)
        self._optimizer.__exit__(ex_type, ex_val, ex_tb)
        self._experiment = None
        return False  # Do not suppress exceptions

    @abstractmethod
    def start(self) -> None:
        """Start the scheduling loop."""
        assert self.experiment is not None
        _LOG.info(
            "START: Experiment: %s Env: %s Optimizer: %s",
            self._experiment,
            self.root_environment,
            self.optimizer,
        )
        if _LOG.isEnabledFor(logging.INFO):
            _LOG.info("Root Environment:\n%s", self.root_environment.pprint())

        if self._config_id > 0:
            tunables = self.load_tunable_config(self._config_id)
            self.schedule_trial(tunables)

    def teardown(self) -> None:
        """
        Tear down the TrialRunners/Environment(s).

        Call it after the completion of the `.start()` in the scheduler context.
        """
        assert self.experiment is not None
        if self._do_teardown:
            for trial_runner in self.trial_runners:
                assert not trial_runner.is_running
                trial_runner.teardown()

    def get_best_observation(self) -> Tuple[Optional[Dict[str, float]], Optional[TunableGroups]]:
        """Get the best observation from the optimizer."""
        (best_score, best_config) = self.optimizer.get_best_observation()
        _LOG.info("Env: %s best score: %s", self.root_environment, best_score)
        return (best_score, best_config)

    def load_tunable_config(self, config_id: int) -> TunableGroups:
        """Load the existing tunable configuration from the storage."""
        assert self.experiment is not None
        tunable_values = self.experiment.load_tunable_config(config_id)
        for environment in self.environments:
            tunables = environment.tunable_params.assign(tunable_values)
        _LOG.info("Load config from storage: %d", config_id)
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Config %d ::\n%s", config_id, json.dumps(tunable_values, indent=2))
        return tunables.copy()

    def _schedule_new_optimizer_suggestions(self) -> bool:
        """
        Optimizer part of the loop.

        Load the results of the executed trials into the optimizer, suggest new
        configurations, and add them to the queue. Return True if optimization is not
        over, False otherwise.
        """
        assert self.experiment is not None
        (trial_ids, configs, scores, status) = self.experiment.load(self._last_trial_id)
        _LOG.info("QUEUE: Update the optimizer with trial results: %s", trial_ids)
        self.optimizer.bulk_register(configs, scores, status)
        self._last_trial_id = max(trial_ids, default=self._last_trial_id)

        not_done = self.not_done()
        if not_done:
            tunables = self.optimizer.suggest()
            self.schedule_trial(tunables)

        return not_done

    def schedule_trial(self, tunables: TunableGroups) -> None:
        """Add a configuration to the queue of trials."""
        # TODO: Alternative scheduling policies may prefer to expand repeats over
        # time as well as space, or adjust the number of repeats (budget) of a given
        # trial based on whether initial results are promising.
        for repeat_i in range(1, self._trial_config_repeat_count + 1):
            self._add_trial_to_queue(
                tunables,
                config={
                    # Add some additional metadata to track for the trial such as the
                    # optimizer config used.
                    # Note: these values are unfortunately mutable at the moment.
                    # Consider them as hints of what the config was the trial *started*.
                    # It is possible that the experiment configs were changed
                    # between resuming the experiment (since that is not currently
                    # prevented).
                    "optimizer": self.optimizer.name,
                    "repeat_i": repeat_i,
                    "is_defaults": tunables.is_defaults(),
                    **{
                        f"opt_{key}_{i}": val
                        for (i, opt_target) in enumerate(self.optimizer.targets.items())
                        for (key, val) in zip(["target", "direction"], opt_target)
                    },
                },
            )

    def _add_trial_to_queue(
        self,
        tunables: TunableGroups,
        ts_start: Optional[datetime] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a configuration to the queue of trials in the Storage backend.

        A wrapper for the `Experiment.new_trial` method.
        """
        assert self.experiment is not None
        trial = self.experiment.new_trial(tunables, ts_start, config)
        # Select a TrialRunner based on the trial's metadata.
        # TODO: May want to further split this in the future to support scheduling a
        # batch of new trials.
        trial_runner = self._assign_trial_runner(trial, trial_runner=None)
        _LOG.info("QUEUE: Added new trial: %s (assigned to %s)", trial, trial_runner)

    def _run_schedule(self, running: bool = False) -> None:
        """
        Scheduler part of the loop.

        Check for pending trials in the queue and run them.
        """
        assert self.experiment is not None
        for trial in self.experiment.pending_trials(datetime.now(UTC), running=running):
            self.run_trial(trial)

    def not_done(self) -> bool:
        """
        Check the stopping conditions.

        By default, stop when the optimizer converges or max limit of trials reached.
        """
        return self.optimizer.not_converged() and (
            self._trial_count < self._max_trials or self._max_trials <= 0
        )

    @abstractmethod
    def run_trial(self, trial: Storage.Trial) -> None:
        """
        Set up and run a single trial.

        Save the results in the storage.
        """
        assert self.experiment is not None
        self._trial_count += 1
        self._ran_trials.append(trial)
        _LOG.info("QUEUE: Execute trial # %d/%d :: %s", self._trial_count, self._max_trials, trial)

    @property
    def ran_trials(self) -> List[Storage.Trial]:
        """Get the list of trials that were run."""
        return self._ran_trials
