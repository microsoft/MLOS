#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Simple class to run an individual Trial on a given Environment.
"""

from typing import Any, Dict, Literal, Optional, Tuple

from datetime import datetime
import logging

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
    in parallel.
    """

    def __init__(self, trial_runner_id: int, env: Environment) -> None:
        self._trial_runner_id = trial_runner_id
        self._env = env
        assert self._env.parameters["trial_runner_id"] == self._trial_runner_id
        self._in_context = False
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

    # TODO: improve context mangement support

    def __enter__(self) -> "TrialRunner":
        assert not self._in_context
        # TODO: Improve logging.
        self._event_loop_context.enter()
        self._env.__enter__()
        self._in_context = True
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> Literal[False]:
        assert self._in_context
        # TODO: Improve logging.
        self._env.__exit__(exc_type, exc_value, traceback)
        self._event_loop_context.exit()
        self._in_context = False
        return False  # Do not suppress exceptions

    def run(self,
            trial: Storage.Trial,
            global_config: Optional[Dict[str, Any]] = None) -> Tuple[Status, Optional[Dict[str, float]]]:
        """
        Run a single trial on this TrialRunner's Environment.

        Parameters
        ----------
        trial : Storage.Trial
            A Storage class based Trial used to persist the experiment data.
        global_config : dict
            Global configuration parameters.

        Returns
        -------
        (trial_status, trial_score) : (Status, Optional[Dict[str, float]])
            Status and results of the trial.
        """
        assert self._in_context
        _LOG.info("Trial: %s", trial)

        if not self._env.setup(trial.tunables, trial.config(global_config)):
            _LOG.warning("Setup failed: %s :: %s", self._env, trial.tunables)
            # FIXME: Use the actual timestamp from the environment.
            trial.update(Status.FAILED, datetime.utcnow())
            return (Status.FAILED, None)

        # TODO: start background status polling of the environments in the event loop.

        (status, timestamp, results) = self._env.run()  # Block and wait for the final result.
        _LOG.info("Results: %s :: %s\n%s", trial.tunables, status, results)

        # In async mode (TODO), poll the environment for status and telemetry
        # and update the storage with the intermediate results.
        (_status, _timestamp, telemetry) = self._env.status()

        # Use the status and timestamp from `.run()` as it is the final status of the experiment.
        # TODO: Use the `.status()` output in async mode.
        trial.update_telemetry(status, timestamp, telemetry)

        trial.update(status, timestamp, results)
        # Filter out non-numeric scores from the optimizer.
        scores = results if not isinstance(results, dict) \
            else {k: float(v) for (k, v) in results.items() if isinstance(v, (int, float))}
        return (status, scores)
