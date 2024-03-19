#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base class for the optimization loop scheduling policies.
"""

import json
import logging
from datetime import datetime

from abc import ABCMeta, abstractmethod
from types import TracebackType
from typing import Any, Dict, List, Iterable, Optional, Tuple, Type
from typing_extensions import Literal

from pytz import UTC

from mlos_bench.environments.base_environment import Environment
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.schedulers.trial_runner import TrialRunner
from mlos_bench.util import merge_parameters

_LOG = logging.getLogger(__name__)


class Scheduler(metaclass=ABCMeta):
    # pylint: disable=too-many-instance-attributes
    """
    Base class for the optimization loop scheduling policies.
    """

    def __init__(self, *,
                 config: Dict[str, Any],
                 global_config: Dict[str, Any],
                 trial_runners: List[TrialRunner],
                 optimizer: Optimizer,
                 storage: Storage,
                 root_env_config: str):
        """
        Create a new instance of the scheduler. The constructor of this
        and the derived classes is called by the persistence service
        after reading the class JSON configuration. Other objects like
        the TrialRunner(s) and their Environment(s) and Optimizer are
        provided by the Launcher.

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
        config = merge_parameters(dest=config.copy(), source=global_config,
                                  required_keys=["experiment_id", "trial_id"])

        self._experiment_id = config["experiment_id"].strip()
        self._trial_id = int(config["trial_id"])
        self._config_id = int(config.get("config_id", -1))

        self._trial_config_repeat_count = int(config.get("trial_config_repeat_count", 1))
        if self._trial_config_repeat_count <= 0:
            raise ValueError(f"Invalid trial_config_repeat_count: {self._trial_config_repeat_count}")

        self._do_teardown = bool(config.get("teardown", True))

        self._experiment: Optional[Storage.Experiment] = None
        self._trial_runners = trial_runners
        assert self._trial_runners, "At least one TrialRunner is required"
        self._optimizer = optimizer
        self._storage = storage
        self._root_env_config = root_env_config
        self._current_trial_runner_idx = 0

        _LOG.debug("Scheduler instantiated: %s :: %s", self, config)

    @property
    def experiment(self) -> Optional[Storage.Experiment]:
        """Gets the Experiment Storage."""
        return self._experiment

    @property
    def root_environment(self) -> Environment:
        """
        Gets the root (prototypical) Environment from the first TrialRunner.

        Note: This all TrialRunners have the same Environment config and are made
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
            raise ValueError(f"Trial {trial} has no trial_runner_id")
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

    def __enter__(self) -> 'Scheduler':
        """
        Enter the scheduler's context.
        """
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
            opt_target=self._optimizer.target,
            opt_direction=self._optimizer.direction,
        ).__enter__()
        return self

    def __exit__(self,
                 ex_type: Optional[Type[BaseException]],
                 ex_val: Optional[BaseException],
                 ex_tb: Optional[TracebackType]) -> Literal[False]:
        """
        Exit the context of the scheduler.
        """
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
        """
        Start the scheduling loop.
        """
        assert self.experiment is not None
        _LOG.info("START: Experiment: %s Env: %s Optimizer: %s",
                  self._experiment, self.root_environment, self.optimizer)
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

    def get_best_observation(self) -> Tuple[Optional[float], Optional[TunableGroups]]:
        """
        Get the best observation from the optimizer.
        """
        (best_score, best_config) = self.optimizer.get_best_observation()
        _LOG.info("Env: %s best score: %s", self.root_environment, best_score)
        return (best_score, best_config)

    def load_tunable_config(self, config_id: int) -> TunableGroups:
        """
        Load the existing tunable configuration from the storage.
        """
        assert self.experiment is not None
        tunable_values = self.experiment.load_tunable_config(config_id)
        for environment in self.environments:
            tunables = environment.tunable_params.assign(tunable_values)
        _LOG.info("Load config from storage: %d", config_id)
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Config %d ::\n%s", config_id, json.dumps(tunable_values, indent=2))
        return tunables.copy()

    def _get_optimizer_suggestions(self, last_trial_id: int = -1, is_warm_up: bool = False) -> int:
        """
        Optimizer part of the loop. Load the results of the executed trials
        into the optimizer, suggest new configurations, and add them to the queue.
        Return the last trial ID processed by the optimizer.
        """
        assert self.experiment is not None
        # FIXME: In async mode, trial_ids may be returned out of order, so we may
        # need to adjust this fetching logic.
        (trial_ids, configs, scores, status) = self.experiment.load(last_trial_id)
        _LOG.info("QUEUE: Update the optimizer with trial results: %s", trial_ids)
        self.optimizer.bulk_register(configs, scores, status, is_warm_up)

        tunables = self.optimizer.suggest()
        self.schedule_trial(tunables)

        return max(trial_ids, default=last_trial_id)

    def schedule_trial(self, tunables: TunableGroups) -> None:
        """
        Add a configuration to the queue of trials.
        """
        # TODO: Alternative scheduling policies may prefer to expand repeats over
        # time as well as space, or adjust the number of repeats (budget) of a given
        # trial based on whether initial results are promising.
        for repeat_i in range(1, self._trial_config_repeat_count + 1):
            self._add_trial_to_queue(tunables, config={
                # Add some additional metadata to track for the trial such as the
                # optimizer config used.
                # Note: these values are unfortunately mutable at the moment.
                # Consider them as hints of what the config was the trial *started*.
                # It is possible that the experiment configs were changed
                # between resuming the experiment (since that is not currently
                # prevented).
                # TODO: Improve for supporting multi-objective
                # (e.g., opt_target_1, opt_target_2, ... and opt_direction_1, opt_direction_2, ...)
                "optimizer": self.optimizer.name,
                "opt_target": self.optimizer.target,
                "opt_direction": self.optimizer.direction,
                "repeat_i": repeat_i,
                "is_defaults": tunables.is_defaults,
                "trial_runner_id": self._trial_runners[self._current_trial_runner_idx].trial_runner_id,
            })
            # Rotate which TrialRunner the Trial is assigned to.
            self._current_trial_runner_idx = (self._current_trial_runner_idx + 1) % len(self._trial_runners)

    def _add_trial_to_queue(self, tunables: TunableGroups,
                            ts_start: Optional[datetime] = None,
                            config: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a configuration to the queue of trials in the Storage backend.
        A wrapper for the `Experiment.new_trial` method.
        """
        assert self.experiment is not None
        trial = self.experiment.new_trial(tunables, ts_start, config)
        _LOG.info("QUEUE: Add new trial: %s", trial)

    def _run_schedule(self, running: bool = False) -> None:
        """
        Scheduler part of the loop. Check for pending trials in the queue and run them.
        """
        assert self.experiment is not None
        for trial in self.experiment.pending_trials(datetime.now(UTC), running=running):
            self.run_trial(trial)

    @abstractmethod
    def run_trial(self, trial: Storage.Trial) -> None:
        """
        Set up and run a single trial. Save the results in the storage.
        """
        assert self.experiment is not None
        _LOG.info("QUEUE: Execute trial: %s", trial)
