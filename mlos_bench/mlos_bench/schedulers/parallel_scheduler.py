#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A simple multi-threaded asynchronous optimization loop implementation."""

import asyncio
import logging
from concurrent.futures import Future, ProcessPoolExecutor
from datetime import datetime
from typing import Any

from pytz import UTC

from mlos_bench.environments.status import Status
from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class ParallelScheduler(Scheduler):
    """A simple multi-threaded asynchronous optimization loop implementation."""

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
            self._run_callbacks()
            self._run_schedule(is_warm_up)
            not_done = self._schedule_new_optimizer_suggestions()
            is_warm_up = False

    def teardown(self) -> None:
        """Stop the optimization loop."""
        # Shutdown the thread pool and wait for all tasks to finish
        self.pool.shutdown(wait=True)
        self._run_callbacks()
        super().teardown()

    def schedule_trial(self, tunables: TunableGroups) -> None:
        """Assign a trial to a trial runner."""
        assert self.experiment is not None

        super().schedule_trial(tunables)

        pending_trials: list[Storage.Trial] = list(
            self.experiment.pending_trials(datetime.now(UTC), running=False)
        )

        idle_runner_ids = [
            id for id, runner in self.trial_runners.items() if not runner.is_running
        ]

        # Assign pending trials to idle runners
        for trial, runner_id in zip(pending_trials, idle_runner_ids):
            trial.update(status=Status.SCHEDULED, timestamp=datetime.now(UTC))
            trial.set_trial_runner(runner_id)

    def _run_schedule(self, running: bool = False) -> None:
        """
        Scheduler part of the loop.

        Check for pending trials in the queue and run them.
        """
        assert self.experiment is not None

        scheduled_trials: list[Storage.Trial] = list(
            self.experiment.filter_trials_by_status(datetime.now(UTC), [Status.SCHEDULED])
        )

        for trial in scheduled_trials:
            trial.update(status=Status.READY, timestamp=datetime.now(UTC))
            self.deferred_run_trial(trial)

    def _on_trial_finished_closure(self, trial: Storage.Trial):
        def _on_trial_finished(self: ParallelScheduler, result: Future) -> None:
            """
            Callback to be called when a trial is finished.

            This must always be called from the main thread. Exceptions can also be handled
            here
            """
            try:
                (status, timestamp, results, telemetry) = result.result()
                self.get_trial_runner(trial)._finalize_run_trial(
                    trial, status, timestamp, results, telemetry
                )
            except Exception as exception:  # pylint: disable=broad-except
                _LOG.error("Trial failed: %s", exception)

        return _on_trial_finished

    @staticmethod
    def _run_callbacks() -> None:
        """Run all pending callbacks in the main thread."""
        loop = asyncio.get_event_loop()
        pending = asyncio.all_tasks(loop)
        loop.run_until_complete(asyncio.gather(*pending))

    def run_trial(self, trial: Storage.Trial) -> None:
        """
        Parallel Scheduler does not support run_trial. Use async_run_trial instead.

        Parameters
        ----------
        trial : Storage.Trial
            The trial to run.

        Raises
        ------
        NotImplementedError
            Error to indicate that this method is not supported in ParallelScheduler.
        """
        raise NotImplementedError(
            "ParallelScheduler does not support run_trial. Use async_run_trial instead."
        )

    def deferred_run_trial(self, trial: Storage.Trial) -> None:
        """
        Set up and run a single trial asynchronously.

        Returns a callback to save the results in the storage.
        """
        super().run_trial(trial)
        # In the sync scheduler we run each trial on its own TrialRunner in sequence.
        trial_runner = self.get_trial_runner(trial)
        trial_runner._prepare_run_trial(trial, self.global_config)

        task = self.pool.submit(trial_runner._execute_run_trial, trial_runner.environment)
        # This is required to ensure that the callback happens on the main thread
        asyncio.get_event_loop().call_soon_threadsafe(
            self._on_trial_finished_closure(trial), self, task
        )

        _LOG.info("QUEUE: Finished trial: %s on %s", trial, trial_runner)
