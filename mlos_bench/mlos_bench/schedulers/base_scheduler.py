#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base class for the optimization loop scheduling policies.
"""

import json
import logging
from datetime import datetime, UTC

from abc import ABCMeta, abstractmethod
from types import TracebackType
from typing import Any, Dict, Optional, Tuple, Type
from typing_extensions import Literal

from mlos_bench.environments.base_environment import Environment
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable_groups import TunableGroups
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
                 environment: Environment,
                 optimizer: Optimizer,
                 storage: Storage,
                 root_env_config: str):
        """
        Create a new instance of the scheduler. The constructor of this
        and the derived classes is called by the persistence service
        after reading the class JSON configuration. Other objects like
        the Environment and Optimizer are provided by the Launcher.

        Parameters
        ----------
        config : dict
            The configuration for the scheduler.
        global_config : dict
            he global configuration for the experiment.
        environment : Environment
            The environment to benchmark/optimize.
        optimizer : Optimizer
            The optimizer to use.
        storage : Storage
            The storage to use.
        root_env_config : str
            Path to the root environment configuration.
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

        self.experiment: Optional[Storage.Experiment] = None
        self.environment = environment
        self.optimizer = optimizer
        self.storage = storage
        self._root_env_config = root_env_config

        _LOG.debug("Scheduler instantiated: %s :: %s", self, config)

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
        self.environment.__enter__()
        self.optimizer.__enter__()
        # Start new or resume the existing experiment. Verify that the
        # experiment configuration is compatible with the previous runs.
        # If the `merge` config parameter is present, merge in the data
        # from other experiments and check for compatibility.
        self.experiment = self.storage.experiment(
            experiment_id=self._experiment_id,
            trial_id=self._trial_id,
            root_env_config=self._root_env_config,
            description=self.environment.name,
            tunables=self.environment.tunable_params,
            opt_target=self.optimizer.target,
            opt_direction=self.optimizer.direction,
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
        assert self.experiment is not None
        self.experiment.__exit__(ex_type, ex_val, ex_tb)
        self.optimizer.__exit__(ex_type, ex_val, ex_tb)
        self.environment.__exit__(ex_type, ex_val, ex_tb)
        self.experiment = None
        return False  # Do not suppress exceptions

    @abstractmethod
    def start(self) -> None:
        """
        Start the optimization loop.
        """
        assert self.experiment is not None
        _LOG.info("START: Experiment: %s Env: %s Optimizer: %s",
                  self.experiment, self.environment, self.optimizer)
        if _LOG.isEnabledFor(logging.INFO):
            _LOG.info("Root Environment:\n%s", self.environment.pprint())

        if self._config_id > 0:
            tunables = self.load_config(self._config_id)
            self.schedule_trial(tunables)

    def teardown(self) -> None:
        """
        Tear down the environment.
        Call it after the completion of the `.start()` in the scheduler context.
        """
        assert self.experiment is not None
        if self._do_teardown:
            self.environment.teardown()

    def get_best_observation(self) -> Tuple[Optional[float], Optional[TunableGroups]]:
        """
        Get the best observation from the optimizer.
        """
        (best_score, best_config) = self.optimizer.get_best_observation()
        _LOG.info("Env: %s best score: %s", self.environment, best_score)
        return (best_score, best_config)

    def load_config(self, config_id: int) -> TunableGroups:
        """
        Load the existing tunable configuration from the storage.
        """
        assert self.experiment is not None
        tunable_values = self.experiment.load_tunable_config(config_id)
        tunables = self.environment.tunable_params.assign(tunable_values)
        _LOG.info("Load config from storage: %d", config_id)
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Config %d ::\n%s", config_id, json.dumps(tunable_values, indent=2))
        return tunables

    def _get_optimizer_suggestions(self, last_trial_id: int = -1, is_warm_up: bool = False) -> int:
        """
        Optimizer part of the loop. Load the results of the executed trials
        into the optimizer, suggest new configurations, and add them to the queue.
        Return the last trial ID processed by the optimizer.
        """
        assert self.experiment is not None
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
            })

    def _add_trial_to_queue(self, tunables: TunableGroups,
                            ts_start: Optional[datetime] = None,
                            config: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a configuration to the queue of trials.
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
