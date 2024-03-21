#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Simple class to run an individual Trial on a given Environment.
"""

from types import TracebackType
from typing import Any, Dict, Literal, Optional, Type

from datetime import datetime
import logging

from pytz import UTC

from mlos_bench.environments.base_environment import Environment
from mlos_bench.environments.status import Status
from mlos_bench.storage.base_storage import Storage
from mlos_bench.event_loop_context import EventLoopContext


_LOG = logging.getLogger(__name__)


class TrialRunner:
    """
    Simple class to help run an individual Trial on an environment.

    TrialRunner manages the lifecycle of a single trial, including setup, run, teardown,
    and async status polling via EventLoopContext background threads.

    Multiple TrialRunners can be used in a multi-processing pool to run multiple trials
    in parallel, for instance.
    """

    def __init__(self, trial_runner_id: int, env: Environment) -> None:
        self._trial_runner_id = trial_runner_id
        self._env = env
        assert self._env.parameters["trial_runner_id"] == self._trial_runner_id
        self._in_context = False
        self._is_running = False
        self._event_loop_context = EventLoopContext()

    @property
    def trial_runner_id(self) -> int:
        """
        Get the TrialRunner's id.
        """
        return self._trial_runner_id

    @property
    def environment(self) -> Environment:
        """
        Get the Environment.
        """
        return self._env

    def __enter__(self) -> "TrialRunner":
        assert not self._in_context
        _LOG.debug("TrialRunner START :: %s", self)
        # TODO: self._event_loop_context.enter()
        self._env.__enter__()
        self._in_context = True
        return self

    def __exit__(self,
                 ex_type: Optional[Type[BaseException]],
                 ex_val: Optional[BaseException],
                 ex_tb: Optional[TracebackType]) -> Literal[False]:
        assert self._in_context
        _LOG.debug("TrialRunner END :: %s", self)
        self._env.__exit__(ex_type, ex_val, ex_tb)
        # TODO: self._event_loop_context.exit()
        self._in_context = False
        return False  # Do not suppress exceptions

    @property
    def is_running(self) -> bool:
        """Get the running state of the current TrialRunner."""
        return self._is_running

    def run_trial(self,
                  trial: Storage.Trial,
                  global_config: Optional[Dict[str, Any]] = None) -> None:
        """
        Run a single trial on this TrialRunner's Environment and stores the results
        in the backend Trial Storage.

        Parameters
        ----------
        trial : Storage.Trial
            A Storage class based Trial used to persist the experiment trial data.
        global_config : dict
            Global configuration parameters.

        Returns
        -------
        (trial_status, trial_score) : (Status, Optional[Dict[str, float]])
            Status and results of the trial.
        """
        assert self._in_context

        assert not self._is_running
        self._is_running = True

        assert trial.trial_runner_id == self.trial_runner_id, \
            f"TrialRunner {self} should not run trial {trial} with different trial_runner_id {trial.trial_runner_id}."

        if not self.environment.setup(trial.tunables, trial.config(global_config)):
            _LOG.warning("Setup failed: %s :: %s", self.environment, trial.tunables)
            # FIXME: Use the actual timestamp from the environment.
            _LOG.info("TrialRunner: Update trial results: %s :: %s", trial, Status.FAILED)
            trial.update(Status.FAILED, datetime.now(UTC))
            return

        # TODO: start background status polling of the environments in the event loop.

        (status, timestamp, results) = self.environment.run()  # Block and wait for the final result.
        _LOG.info("TrialRunner Results: %s :: %s\n%s", trial.tunables, status, results)

        # In async mode (TODO), poll the environment for status and telemetry
        # and update the storage with the intermediate results.
        (_status, _timestamp, telemetry) = self.environment.status()

        # Use the status and timestamp from `.run()` as it is the final status of the experiment.
        # TODO: Use the `.status()` output in async mode.
        trial.update_telemetry(status, timestamp, telemetry)

        trial.update(status, timestamp, results)
        _LOG.info("TrialRunner: Update trial results: %s :: %s %s", trial, status, results)

        self._is_running = False

    def teardown(self) -> None:
        """
        Tear down the Environment.
        Call it after the completion of one (or more) `.run()` in the TrialRunner context.
        """
        assert self._in_context
        self._env.teardown()
