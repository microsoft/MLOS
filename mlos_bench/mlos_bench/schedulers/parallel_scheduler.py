#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A simple multi-threaded asynchronous optimization loop implementation."""

import asyncio
import logging
from collections.abc import Callable
from concurrent.futures import Future, ProcessPoolExecutor
from datetime import datetime
from typing import Any

from pytz import UTC

from mlos_bench.environments.status import Status
from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.schedulers.trial_runner import TrialRunner
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class ParallelScheduler(Scheduler):
    """A simple multi-process asynchronous optimization loop implementation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:

        super().__init__(*args, **kwargs)
        self.pool = ProcessPoolExecutor(max_workers=len(self._trial_runners))

    def start(self) -> None:
        """Start the optimization loop."""
        super().start()

        is_warm_up: bool = self.optimizer.supports_preload
        if not is_warm_up:
            _LOG.warning("Skip pending trials and warm-up: %s", self.optimizer)

        not_done: bool = True
        while not_done:
            _LOG.info("Optimization loop: Last trial ID: %d", self._last_trial_id)
            self._run_schedule(is_warm_up)
            not_done = self._schedule_new_optimizer_suggestions()
            pending_trials = self.experiment.pending_trials(datetime.now(UTC), running=False)
            self.assign_trial_runners(pending_trials)
            is_warm_up = False

    def _teardown_trial_runner(
        self,
        trial_runner_id: int,
    ) -> TrialRunnerResult:
        """Tear down a specific TrialRunner in a Pool worker."""
        assert self._pool is None, "This should only be called in a Pool worker."
        trial_runner = self._trial_runners[trial_runner_id]
        with trial_runner:
            return TrialRunnerResult(
                trial_runner_id=trial_runner_id,
                result=trial_runner.teardown(),
            )

    def _teardown_trial_runner_finished_callback(
        self,
        result: TrialRunnerResult,
    ) -> None:
        """Callback to be called when a TrialRunner is finished with teardown."""
        trial_runner_id = result.trial_runner_id
        assert trial_runner_id in self._trial_runners_status
        assert self._trial_runners_status[trial_runner_id] is not None
        self._trial_runners_status[result.trial_runner_id] = None

    def _teardown_trial_runner_failed_closure(
        self,
        trial_runner_id: int,
    ) -> Callable[[Any], None]:
        # pylint: disable=no-self-use
        """Callback to be called when a TrialRunner failed running teardown."""

        def _teardown_trial_runner_failed(obj: Any) -> None:
            """Callback to be called when a TrialRunner failed running teardown."""
            # TODO: improve error handling here
            _LOG.error("TrialRunner %d failed to run teardown: %s", trial_runner_id, obj)
            raise RuntimeError(f"TrialRunner {trial_runner_id} failed to run teardown: {obj}")

        return _teardown_trial_runner_failed

    def run_trial(self, trial: Storage.Trial) -> None:
        """
        Set up and run a single Trial on a TrialRunner in a child process in the pool.

        Save the results in the storage.
        """
        assert self._pool is None, "This should only be called in a Pool worker."
        super().run_trial(trial)
        # In the sync scheduler we run each trial on its own TrialRunner in sequence.
        trial_runner = self.get_trial_runner(trial)
        with trial_runner:
            trial_runner.run_trial(trial, self.global_config)
            _LOG.info("QUEUE: Finished trial: %s on %s", trial, trial_runner)

    def run_trial_on_trial_runner(
        self,
        trial_runner: TrialRunner,
        storage: Storage,
        experiment_id: str,
        trial_id: int,
    ):
        """Run a single trial on a TrialRunner in a child process in the pool.

        Save the results in the storage.
        """

    def _run_schedule(self, running: bool = False) -> None:
        assert self._pool is not None

        pending_trials = self.experiment.pending_trials(datetime.now(UTC), running=running)
        scheduled_trials = [
            pending_trial
            for pending_trial in pending_trials
            if pending_trial.trial_runner_id is not None and pending_trial.trial_runner_id >= 0
        ]

        for trial in scheduled_trials:
            trial_runner_id = trial.trial_runner_id
            assert trial_runner_id is not None
            trial_runner_status = self._trial_runners_status[trial_runner_id]
            if trial_runner_status is not None:
                _LOG.warning(
                    "Cannot start Trial %d - its assigned TrialRunner %d is already running: %s",
                    trial.trial_id,
                    trial_runner_id,
                    trial_runner_status,
                )
                continue

            # Update our trial bookkeeping.
            super().run_trial(trial)
            # Run the trial in the child process targeting a particular runner.
            # TODO:

        # Wait for all trial runners to finish.
        while self._has_running_trial_runners():
            sleep(self._polling_interval)
        assert self._get_idle_trial_runners_count() == len(self._trial_runners)

    def _teardown_trial_runner(
        self,
        trial_runner_id: int,
    ) -> TrialRunnerResult:
        """Tear down a specific TrialRunner in a Pool worker."""
        assert self._pool is None, "This should only be called in a Pool worker."
        trial_runner = self._trial_runners[trial_runner_id]
        with trial_runner:
            return TrialRunnerResult(
                trial_runner_id=trial_runner_id,
                result=trial_runner.teardown(),
            )

    def _teardown_trial_runner_finished_callback(
        self,
        result: TrialRunnerResult,
    ) -> None:
        """Callback to be called when a TrialRunner is finished with teardown."""
        trial_runner_id = result.trial_runner_id
        assert trial_runner_id in self._trial_runners_status
        assert self._trial_runners_status[trial_runner_id] is not None
        self._trial_runners_status[result.trial_runner_id] = None

    def _teardown_trial_runner_failed_closure(
        self,
        trial_runner_id: int,
    ) -> Callable[[Any], None]:
        # pylint: disable=no-self-use
        """Callback to be called when a TrialRunner failed running teardown."""

        def _teardown_trial_runner_failed(obj: Any) -> None:
            """Callback to be called when a TrialRunner failed running teardown."""
            # TODO: improve error handling here
            _LOG.error("TrialRunner %d failed to run teardown: %s", trial_runner_id, obj)
            raise RuntimeError(f"TrialRunner {trial_runner_id} failed to run teardown: {obj}")

        return _teardown_trial_runner_failed

    def teardown(self) -> None:
        assert self._pool is not None
        if self._do_teardown:
            # Call teardown on each TrialRunner in the pool in parallel.
            for trial_runner_id in self._trial_runners:
                assert (
                    self._trial_runners_status[trial_runner_id] is None
                ), f"TrialRunner {trial_runner_id} is still active."
                self._trial_runners_status[trial_runner_id] = self._pool.apply_async(
                    # Call the teardown function in the child process targeting
                    # a particular trial_runner_id.
                    self._teardown_trial_runner,
                    args=(trial_runner_id,),
                    callback=self._teardown_trial_runner_finished_callback,
                    error_callback=self._teardown_trial_runner_failed_closure(trial_runner_id),
                )

        # Wait for all trial runners to finish.
        while self._has_running_trial_runners():
            sleep(self._polling_interval)
        assert self._get_idle_trial_runners_count() == len(self._trial_runners)

    def assign_trial_runners(self, trials: Iterable[Storage.Trial]) -> None:
        """
        Assign Trials to the first available and idle TrialRunner.

        Parameters
        ----------
        trials : Iterable[Storage.Trial]
        """
        assert self._in_context
        assert self.experiment is not None

        pending_trials: list[Storage.Trial] = list(
            trial
            for trial in trials
            if trial.status.is_pending() and trial.trial_runner_id is None
        )

        idle_runner_ids = [
            trial_runner_id
            for trial_runner_id, status in self._trial_runners_status.items()
            if status is None
        ]

        # Assign pending trials to idle runners
        for trial, runner_id in zip(pending_trials, idle_runner_ids):
            # FIXME: This results in two separate non-transactional updates.
            # Should either set Status=SCHEDULED when we set_trial_runner
            # or remove SCHEDULED as a Status altogether and filter by
            # "Status=PENDING AND trial_runner_id != NULL"
            # Or ... even better, we could use a single transaction to update
            # the status and trial_runner_id of all trials in the same batch at once.
            trial.set_trial_runner(runner_id)
            # Moreover this doesn't even update the status of the Trial - it only updates the telemetry.
            trial.update(status=Status.SCHEDULED, timestamp=datetime.now(UTC))
