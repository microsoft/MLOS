#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A simple multi-process asynchronous optimization loop implementation.

TODO: Add more details about the design and constraints and gotchas here.

Examples
--------
TODO: Add config examples here.
"""

import logging
from collections.abc import Callable, Iterable
from multiprocessing import current_process as mp_proccess_name
from multiprocessing.pool import AsyncResult, Pool
from datetime import datetime
from typing import Any
from time import sleep

from attr import dataclass
from pytz import UTC

from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.schedulers.trial_runner import TrialRunner
from mlos_bench.storage.base_storage import Storage
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.tunables.tunable_types import TunableValue

_LOG = logging.getLogger(__name__)


def _is_child_process() -> bool:
    """Check if the current process is a child process."""
    return mp_proccess_name() != "MainProcess"


@dataclass
class TrialRunnerResult:
    """A simple data class to hold the :py:class:`AsyncResult` of a
    :py:class:`TrialRunner` operation."""

    trial_runner_id: int
    result: dict[str, TunableValue] | None
    trial_id: int | None = None


class ParallelScheduler(Scheduler):
    """A simple multi-process asynchronous optimization loop implementation.

    See :py:mod:`mlos_bench.schedulers.parallel_scheduler` for more usage details.

    Notes
    -----
    This schedule uses :ext:py:class:`multiprocessing.Pool` to run trials in parallel.

    To avoid issues with Python's forking implementation, which relies on pickling
    objects from the main process and sending them to the child process, we need
    to avoid incompatible objects, which includes any additional threads (e.g.,
    :py:mod:`asyncio` tasks such as
    :py:class:`mlos_bench.event_loop_context.EventLoopContext`), database
    connections (e.g., :py:mod:`mlos_bench.storage`), and file handles (e.g.,
    :ext:py:mod:`logging`) that are pickle incompatible.

    To accomplish this, we avoid entering the :py:class:`~.TrialRunner` context
    until we are in the child process and allow each child to manage its own
    incompatible resources via that context.

    Hence, each child process in the pool actually starts in functions in
    special handler functions in the :py:class:`~.ParallelScheduler` class that
    receive as inputs all the necessary (and picklable) info as arguments, then
    enter the given :py:class:`~.TrialRunner` instance context and invoke that
    procedure.
    """

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
        super().__init__(
            config=config,
            global_config=global_config,
            trial_runners=trial_runners,
            optimizer=optimizer,
            storage=storage,
            root_env_config=root_env_config,
        )

        self._polling_interval: float = config.get("polling_interval", 1.0)

        # TODO: Setup logging for the child processes via a logging queue.

        self._pool: Pool | None = None
        """Parallel pool to run Trials in separate TrialRunner processes.

        Only initiated on context __enter__.
        """

        self._trial_runners_status: dict[int, AsyncResult[TrialRunnerResult] | None] = {
            trial_runner.trial_runner_id: None for trial_runner in self._trial_runners.values()
        }
        """A dict to keep track of the status of each TrialRunner.

        Since TrialRunners enter their running context within each pool task, we
        can't check :py:meth:`.TrialRunner.is_running` within the parent
        generally.

        Instead, we use a dict to keep track of the status of each TrialRunner
        as either None (idle) or AsyncResult (running).

        This also helps us to gather AsyncResults from each worker.
        """

    def _get_idle_trial_runners_count(self) -> int:
        return len(
            [
                trial_runner_status
                for trial_runner_status in self._trial_runners_status.values()
                if trial_runner_status is None
            ]
        )

    def _has_running_trial_runners(self) -> bool:
        return any(
            True
            for trial_runner_status in self._trial_runners_status.values()
            if trial_runner_status is not None
        )

    def __enter__(self):
        assert self._pool is None
        self._pool = Pool(processes=len(self.trial_runners), maxtasksperchild=1)
        self._pool.__enter__()
        # Delay context entry in the parent process
        return super().__enter__()

    def __exit__(self, ex_type, ex_val, ex_tb):
        assert self._pool is not None
        # Shutdown the process pool and wait for all tasks to finish
        # (everything should be done by now)
        assert self._has_running_trial_runners() is False
        assert self._get_idle_trial_runners_count() == len(self._trial_runners)
        self._pool.close()
        self._pool.join()
        self._pool.__exit__(ex_type, ex_val, ex_tb)
        self._pool = None
        return super().__exit__(ex_type, ex_val, ex_tb)

    # TODO: Consolidate to base_scheduler?
    def start(self) -> None:
        """Start the optimization loop."""
        super().start()
        assert self.experiment is not None

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
