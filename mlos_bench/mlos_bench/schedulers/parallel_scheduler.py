#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A simple single-threaded synchronous optimization loop implementation."""

import copy
import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime
from typing import Optional

from pytz import UTC

from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.storage.base_storage import Storage

_LOG = logging.getLogger(__name__)


class ParallelScheduler(Scheduler):
    """A simple multi-threaded asynchronous optimization loop implementation."""

    def start(self) -> None:
        """Start the optimization loop."""
        super().start()

        self._idle_runners: set[int] = set(self._trial_runners.keys())
        self._busy_runners: set[int] = set()
        self._scheduled_trials: set[int] = set()
        self._pending_updates: list[Callable[[], None]] = []
        self._pending_threads: list[threading.Thread] = []
        self._runner_lock: threading.Lock = threading.Lock()

        is_warm_up: bool = self.optimizer.supports_preload
        if not is_warm_up:
            _LOG.warning("Skip pending trials and warm-up: %s", self.optimizer)

        not_done: bool = True
        while not_done:
            _LOG.info("Optimization loop: Last trial ID: %d", self._last_trial_id)
            self._run_schedule(is_warm_up)
            not_done = self._schedule_new_optimizer_suggestions()
            is_warm_up = False

        # Wait for all pending runners to finish
        while len(self._busy_runners) > 0:
            with self._runner_lock:
                for update in self._pending_updates:
                    update()
            time.sleep(1)

    def _run_schedule(self, running: bool = False) -> None:
        """
        Scheduler part of the loop.

        Check for pending trials in the queue and run them.
        """
        assert self.experiment is not None
        # Collect all pending trials
        # It is critical that we filter out trials that are already assigned to a trial runner
        # If we do not filter out these trials, it will cause configurations to be double scheduled
        # and will cause the storage backend to fail.
        pending_trials: list[Storage.Trial] = [
            t
            for t in self.experiment.pending_trials(datetime.now(UTC), running=running)
            if t.trial_id not in self._scheduled_trials
        ]

        for trial in pending_trials:
            # Wait for an idle trial runner
            trial_runner_id: int | None = None
            while trial_runner_id is None:
                with self._runner_lock:
                    for update in self._pending_updates:
                        update()
                    self._pending_updates.clear()
                    if len(self._idle_runners) > 0:
                        # Schedule a Trial to a Trial Runner
                        trial_runner_id = self._idle_runners.pop()
                        self._busy_runners.add(trial_runner_id)
                        self._scheduled_trials.add(trial.trial_id)

                        # Assign the trial to the trial runner. Note that this will be reset
                        # if pending_trials is queried again from the experiment
                        trial.set_trial_runner(trial_runner_id)
                        self.run_trial(trial)

                if trial_runner_id is None:
                    # Sleep for a short time if failed to find to prevent busy wait
                    _LOG.debug("No idle trial runners available. Waiting...")
                    time.sleep(1)

    def async_run_trial(self, trial: Storage.Trial) -> None:
        """
        Run a single trial in the background.

        Parameters
        ----------
        trial : Storage.Trial
            A Storage class based Trial used to persist the experiment trial data.
        """
        register_fn = self.get_trial_runner(trial)._run_trial(trial, copy.copy(self.global_config))

        def callback(trial: Storage.Trial = trial):
            """
            Callback to pass to the main thread to register the results with the
            storage.

            Parameters
            ----------
            trial : Storage.Trial
                A Storage class based Trial used to persist the experiment trial data.
            """
            assert trial.trial_runner_id is not None, "Trial runner ID should not be None"

            register_fn()
            self._busy_runners.remove(trial.trial_runner_id)
            self._idle_runners.add(trial.trial_runner_id)

        with self._runner_lock:
            self._pending_updates.append(callback)

    def run_trial(self, trial: Storage.Trial) -> None:
        """
        Schedule a single trial to be run in the background.

        Parameters
        ----------
        trial : Storage.Trial
            A Storage class based Trial used to persist the experiment trial data.
        """
        super().run_trial(trial)
        trial_runner = self.get_trial_runner(trial)

        thread = threading.Thread(target=self.async_run_trial, args=(trial,))
        self._pending_threads.append(thread)
        thread.start()
