#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Base class for the optimization loop scheduling policies."""

import json
import logging
from abc import ABCMeta, abstractmethod
from collections.abc import Iterable
from contextlib import AbstractContextManager as ContextManager
from datetime import datetime
from types import TracebackType
from typing import Any, Literal

from pytz import UTC

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.environments.base_environment import Environment
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.schedulers.trial_runner import TrialRunner
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import merge_parameters

_LOG = logging.getLogger(__name__)


class Scheduler(ContextManager, metaclass=ABCMeta):
    # pylint: disable=too-many-instance-attributes
    """Base class for the optimization loop scheduling policies."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        config: dict[str, Any],
        global_config: dict[str, Any],
        trial_runners: Iterable[TrialRunner],
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
        trial_runner : Iterable[TrialRunner]
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

        self._in_context = False
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

        self._experiment: Storage.Experiment | None = None

        assert trial_runners, "At least one TrialRunner is required"
        self._trial_runners = {
            trial_runner.trial_runner_id: trial_runner for trial_runner in trial_runners
        }
        self._current_trial_runner_idx = 0
        self._trial_runner_ids = list(self._trial_runners.keys())
        assert len(self._trial_runner_ids) == len(
            self._trial_runners
        ), f"Duplicate TrialRunner ids detected: {trial_runners}"

        self._optimizer = optimizer
        self._storage = storage
        self._root_env_config = root_env_config
        self._last_trial_id = -1
        self._ran_trials: list[Storage.Trial] = []

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
    def experiment(self) -> Storage.Experiment | None:
        """Gets the Experiment Storage."""
        return self._experiment

    @property
    def root_environment(self) -> Environment:
        """
        Gets the root (prototypical) Environment from the first TrialRunner.

        Notes
        -----
        All TrialRunners have the same Environment config and are made
        unique by their use of the unique trial_runner_id assigned to each
        TrialRunner's Environment's global_config.
        """
        # Use the first TrialRunner's Environment as the root Environment.
        return self._trial_runners[self._trial_runner_ids[0]].environment

    @property
    def trial_runners(self) -> dict[int, TrialRunner]:
        """Gets the set of Trial Runners."""
        return self._trial_runners

    @property
    def environments(self) -> Iterable[Environment]:
        """Gets the Environment from the TrialRunners."""
        return (trial_runner.environment for trial_runner in self._trial_runners.values())

    @property
    def optimizer(self) -> Optimizer:
        """Gets the Optimizer."""
        return self._optimizer

    @property
    def storage(self) -> Storage:
        """Gets the Storage."""
        return self._storage

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
        assert not self._in_context
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
        for trial_runner in self._trial_runners.values():
            trial_runner.__enter__()
        self._in_context = True
        return self

    def __exit__(
        self,
        ex_type: type[BaseException] | None,
        ex_val: BaseException | None,
        ex_tb: TracebackType | None,
    ) -> Literal[False]:
        """Exit the context of the scheduler."""
        if ex_val is None:
            _LOG.debug("Scheduler END :: %s", self)
        else:
            assert ex_type and ex_val
            _LOG.warning("Scheduler END :: %s", self, exc_info=(ex_type, ex_val, ex_tb))
        assert self._in_context
        for trial_runner in self._trial_runners.values():
            trial_runner.__exit__(ex_type, ex_val, ex_tb)
        assert self._experiment is not None
        self._experiment.__exit__(ex_type, ex_val, ex_tb)
        self._optimizer.__exit__(ex_type, ex_val, ex_tb)
        self._experiment = None
        self._in_context = False
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
            for trial_runner in self._trial_runners.values():
                assert not trial_runner.is_running
                trial_runner.teardown()

    def get_best_observation(self) -> tuple[dict[str, float] | None, TunableGroups | None]:
        """Get the best observation from the optimizer."""
        (best_score, best_config) = self.optimizer.get_best_observation()
        _LOG.info("Env: %s best score: %s", self.root_environment, best_score)
        return (best_score, best_config)

    def load_tunable_config(self, config_id: int) -> TunableGroups:
        """Load the existing tunable configuration from the storage."""
        assert self.experiment is not None
        tunable_values = self.experiment.load_tunable_config(config_id)
        tunables = TunableGroups()
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
        ts_start: datetime | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a configuration to the queue of trials in the Storage backend.

        A wrapper for the `Experiment.new_trial` method.
        """
        assert self.experiment is not None
        trial = self.experiment.new_trial(tunables, ts_start, config)
        _LOG.info("QUEUE: Added new trial: %s", trial)

    def assign_trial_runners(self, trials: Iterable[Storage.Trial]) -> None:
        """
        Assigns TrialRunners to the given Trial.

        The base class implements a simple round-robin scheduling algorithm.

        Subclasses can override this method to implement a more sophisticated policy.
        For instance::

            def assign_trial_runners(
                self,
                trials: Iterable[Storage.Trial],
            ) -> TrialRunner:
                trial_runners_map = {}
                # Implement a more sophisticated policy here.
                # For example, to assign the Trial to the TrialRunner with the least
                # number of running Trials.
                # Or assign the Trial to the TrialRunner that hasn't executed this
                # TunableValues Config yet.
                for (trial, trial_runner) in trial_runners_map:
                    # Call the base class method to assign the TrialRunner in the Trial's metadata.
                    trial.set_trial_runner(trial_runner)
                ...

        Parameters
        ----------
        trials : Iterable[Storage.Trial]
            The trial to assign a TrialRunner to.
        """
        for trial in trials:
            if trial.trial_runner_id is not None:
                _LOG.info(
                    "Trial %s already has a TrialRunner assigned: %s",
                    trial,
                    trial.trial_runner_id,
                )
                continue

            # Basic round-robin trial runner assignment policy:
            # fetch and increment the current TrialRunner index.
            # Override in the subclass for a more sophisticated policy.
            trial_runner_idx = self._current_trial_runner_idx
            self._current_trial_runner_idx += 1
            self._current_trial_runner_idx %= len(self._trial_runner_ids)
            trial_runner = self._trial_runners[self._trial_runner_ids[trial_runner_idx]]
            assert trial_runner
            _LOG.info(
                "Assigning TrialRunner %s to Trial %s via basic round-robin policy.",
                trial_runner,
                trial,
            )
            assigned_trial_runner_id = trial.set_trial_runner(trial_runner.trial_runner_id)
            if assigned_trial_runner_id != trial_runner.trial_runner_id:
                raise ValueError(
                    f"Failed to assign TrialRunner {trial_runner} to Trial {trial}: "
                    f"{assigned_trial_runner_id}"
                )

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
            self.assign_trial_runners([trial])
        assert trial.trial_runner_id is not None
        trial_runner = self._trial_runners.get(trial.trial_runner_id)
        if trial_runner is None:
            raise ValueError(
                f"TrialRunner {trial.trial_runner_id} for Trial {trial} "
                f"not found: {self._trial_runners}"
            )
        assert trial_runner.trial_runner_id == trial.trial_runner_id
        return trial_runner

    def _run_schedule(self, running: bool = False) -> None:
        """
        Scheduler part of the loop.

        Check for pending trials in the queue and run them.
        """
        assert self.experiment is not None
        # Make sure that any pending trials have a TrialRunner assigned.
        pending_trials = list(self.experiment.pending_trials(datetime.now(UTC), running=running))
        self.assign_trial_runners(pending_trials)
        for trial in pending_trials:
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
        assert self._in_context
        assert self.experiment is not None
        self._trial_count += 1
        self._ran_trials.append(trial)
        _LOG.info("QUEUE: Execute trial # %d/%d :: %s", self._trial_count, self._max_trials, trial)

    @property
    def ran_trials(self) -> list[Storage.Trial]:
        """Get the list of trials that were run."""
        return self._ran_trials
