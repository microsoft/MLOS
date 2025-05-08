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
from datetime import datetime
from multiprocessing import current_process
from multiprocessing.pool import AsyncResult, Pool
from time import sleep
from typing import Any

from attr import dataclass
from pytz import UTC

from mlos_bench.environments.status import Status
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.schedulers.trial_runner import TrialRunner
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable_types import TunableValue

_LOG = logging.getLogger(__name__)


MAIN_PROCESS_NAME = "MainProcess"
"""Name of the main process in control of the
:external:py:class:`multiprocessing.Pool`.
"""


def is_child_process() -> bool:
    """Check if the current process is a child process."""
    return current_process().name != MAIN_PROCESS_NAME


@dataclass
class TrialRunnerResult:
    """A simple data class to hold the :py:class:`AsyncResult` of a
    :py:class:`TrialRunner` operation.
    """

    trial_runner_id: int
    results: dict[str, TunableValue] | None
    timestamp: datetime | None = None
    status: Status | None = None
    trial_id: int | None = None


class ParallelScheduler(Scheduler):
    """
    A simple multi-process asynchronous optimization loop implementation.

    See :py:mod:`mlos_bench.schedulers.parallel_scheduler` for more usage details.

    Notes
    -----
    This schedule uses :ext:py:class:`multiprocessing.Pool` to run
    :py:class:`~.Storage.Trial`s in parallel.

    To avoid issues with Python's forking implementation, which relies on pickling
    objects and functions from the main process and sending them to the child
    process to invoke, we need to avoid incompatible objects, which includes any
    additional threads (e.g., :py:mod:`asyncio` tasks such as
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

    For instance :py:meth:`~.ParallelScheduler._teardown_trial_runner` is a function that
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

        # TODO: Add schema support for this config.
        self._idle_worker_scheduling_batch_size = int(
            # By default wait for 1 idle workers before scheduling new trials.
            config.get("idle_worker_scheduling_batch_size", 1)
        )
        # Never wait for more than the number of trial runners.
        self._idle_worker_scheduling_batch_size = min(
            self._idle_worker_scheduling_batch_size,
            len(self._trial_runners),
        )
        if self._idle_worker_scheduling_batch_size < 1:
            _LOG.warning(
                "Idle worker scheduling is set to %d, which is less than 1. "
                f"Setting it to number of TrialRunners {len(self._trial_runners)}.",
                self._idle_worker_scheduling_batch_size,
            )
            self._idle_worker_scheduling_batch_size = len(self._trial_runners)

        # TODO: Add schema support for this config.
        self._polling_interval = float(config.get("polling_interval", 1.0))

        # TODO: Setup logging for the child processes via a logging queue.

        self._pool: Pool | None = None
        """
        Parallel :external:py:class:`.Pool` to run :py:class:`~.Storage.Trial`s in
        separate :py:class:`.TrialRunner` processes.

        Only initiated on context :py:meth:`.__enter__`.
        """

        self._trial_runners_status: dict[int, AsyncResult[TrialRunnerResult] | None] = {
            trial_runner.trial_runner_id: None for trial_runner in self._trial_runners.values()
        }
        """
        A dict to keep track of the status of each :py:class:`.TrialRunner`.

        Since TrialRunners enter their running context within each pool task, we
        can't check :py:meth:`.TrialRunner.is_running` within the parent
        generally.

        Instead, we use a dict to keep track of the status of each TrialRunner
        as either None (idle) or AsyncResult (running).

        This also helps us to gather AsyncResults from each worker.
        """

    @property
    def idle_worker_scheduling_batch_size(self) -> int:
        """
        Get the batch size for idle worker scheduling.

        This is the number of idle workers to wait for before scheduling new trials.
        """
        return self._idle_worker_scheduling_batch_size

    def _get_idle_trial_runners_count(self) -> int:
        """
        Return a count of idle trial runners.

        Can be used as a hint for the number of new trials we can run when we next get
        more suggestions from the Optimizer.
        """
        return len(
            [
                trial_runner_status
                for trial_runner_status in self._trial_runners_status.values()
                if trial_runner_status is None
            ]
        )

    def _has_running_trial_runners(self) -> bool:
        """Check to see if any TrialRunners are currently busy."""
        return any(
            True
            for trial_runner_status in self._trial_runners_status.values()
            if trial_runner_status is not None
        )

    def __enter__(self):
        # Setup the process pool to run the trials in parallel.
        self._pool = Pool(processes=len(self.trial_runners), maxtasksperchild=1)
        self._pool.__enter__()
        # Delay context entry in the parent process
        return super().__enter__()

    def __exit__(self, ex_type, ex_val, ex_tb):
        assert self._pool is not None
        # Shutdown the process pool and wait for all tasks to finish
        # (everything should be done by now anyways)
        assert not self._has_running_trial_runners()
        assert self._get_idle_trial_runners_count() == len(self._trial_runners)
        self._pool.close()
        self._pool.join()
        self._pool.__exit__(ex_type, ex_val, ex_tb)
        return super().__exit__(ex_type, ex_val, ex_tb)

    @staticmethod
    def run_trial_on_trial_runner(
        storage: Storage,
        experiment_id: str,
        trial_id: int,
        trial_runner: TrialRunner,
        global_config: dict[str, Any] | None,
    ) -> TrialRunnerResult:
        """
        Retrieve and run a :py:class:`~.Storage.Trial` on a specific
        :py:class:`.TrialRunner` in a :py:class:`~.Pool` background worker process.

        Parameters
        ----------
        storage : Storage
            The :py:class:`~.Storage` to use to retrieve the :py:class:`.Storage.Trial`.
        experiment_id : str
            The ID of the experiment the trial is a part of.
        trial_id : int
            The ID of the trial.
        trial_runner : TrialRunner
            The :py:class:`.TrialRunner` to run on.
        global_config : dict[str, Any] | None
            The global configuration to use for the trial.

        Returns
        -------
        TrialRunnerResult
            The result of the :py:meth:`.TrialRunner.run_trial` operation.

        Notes
        -----
        This is called in the Pool worker process, so it must receive arguments
        that are picklable and be able to construct all necessary state from that.
        Upon completion a callback is used to update the status of the
        TrialRunner in the ParallelScheduler with the value in the
        TrialRunnerResult.
        """
        assert is_child_process(), "This should be called in a Pool worker."
        exp = storage.get_experiment_by_id(experiment_id)
        assert exp is not None, "Experiment not found."
        trial = exp.get_trial_by_id(trial_id)
        assert trial is not None, "Trial not found."
        assert (
            trial.trial_runner_id == trial_runner.trial_runner_id
        ), f"Unexpected Trial Runner {trial_runner} for Trial {trial}."
        with trial_runner:
            (status, ts, results) = trial_runner.run_trial(trial, global_config)
            return TrialRunnerResult(
                trial_runner_id=trial_runner.trial_runner_id,
                results=results,
                timestamp=ts,
                status=status,
                trial_id=trial.trial_id,
            )

    def _run_trial_on_trial_runner_finished_callback(
        self,
        result: TrialRunnerResult,
    ) -> None:
        """Callback to be called when a TrialRunner is finished with run_trial."""
        trial_runner_id = result.trial_runner_id
        assert (
            trial_runner_id in self._trial_runners_status
        ), f"Unexpected TrialRunner {trial_runner_id}."
        assert (
            self._trial_runners_status[trial_runner_id] is not None
        ), f"TrialRunner {trial_runner_id} should have been running."
        # Mark the TrialRunner as finished.
        self._trial_runners_status[result.trial_runner_id] = None
        # TODO: save the results?
        # TODO: Allow scheduling of new trials here.

    def _run_trial_on_trial_runner_failed_closure(
        self,
        trial_runner_id: int,
    ) -> Callable[[Any], None]:
        # pylint: disable=no-self-use
        """Callback to be called when a TrialRunner failed running run_trial."""

        def _run_trial_on_trial_runner_failed(obj: Any) -> None:
            """Callback to be called when a TrialRunner failed running run_trial."""
            # TODO: improve error handling here
            _LOG.error("TrialRunner %d failed on run_trial: %s", trial_runner_id, obj)
            raise RuntimeError(f"TrialRunner {trial_runner_id} failed on run_trial: {obj}")

        return _run_trial_on_trial_runner_failed

    def run_trial(self, trial: Storage.Trial) -> None:
        """
        Set up and run a single Trial on a TrialRunner in a child process in the pool.

        The TrialRunner saves the results in the Storage.
        """
        assert self._pool is not None
        assert self._in_context
        assert not is_child_process(), "This should be called in the parent process."

        # Run the given trial in the child process targeting a particular runner.
        trial_runner_id = trial.trial_runner_id
        assert trial_runner_id is not None, f"Trial {trial} has not been assigned a trial runner."
        trial_runner = self._trial_runners[trial_runner_id]

        if self._trial_runners_status[trial_runner_id] is not None:
            _LOG.info("TrialRunner %s is still active. Skipping trial %s.", trial_runner, trial)

        # Update our trial bookkeeping.
        super().run_trial(trial)
        # Start the trial in a child process.
        self._trial_runners_status[trial_runner_id] = self._pool.apply_async(
            # Call the teardown function in the child process targeting
            # a particular trial_runner.
            self.run_trial_on_trial_runner,
            args=(
                self.storage,
                self._experiment_id,
                trial.trial_id,
                trial_runner,
                self.global_config,
            ),
            callback=self._run_trial_on_trial_runner_finished_callback,
            error_callback=self._run_trial_on_trial_runner_failed_closure(trial_runner_id),
        )

    def run_schedule(self, running: bool = False) -> None:
        """
        Runs the current schedule of Trials on parallel background workers.

        Check for :py:class:`.Trial`s with `:py:attr:`.Status.PENDING` and an
        assigned :py:attr:`~.Trial.trial_runner_id` in the queue and run them
        with :py:meth:`~.Scheduler.run_trial`.
        """

        assert not is_child_process(), "This should be called in the parent process."
        assert self._pool is not None
        assert self._experiment is not None

        scheduled_trials = self._experiment.pending_trials(
            datetime.now(UTC),
            running=running,
            trial_runner_assigned=True,
        )
        scheduled_trials = [
            trial
            for trial in scheduled_trials
            if trial.trial_runner_id is not None and trial.trial_runner_id >= 0
        ]

        # Start each of the scheduled trials in the background.
        for trial in scheduled_trials:
            self.run_trial(trial)
        # Now all available trial should be started in the background.
        # We can move on to wait_trial_runners() to wait for some to finish.

    def wait_for_trial_runners(self, wait_all: bool = False) -> None:
        """
        Wait for all :py:class:`.TrialRunner`s to finish running.

        This is a blocking call that will wait for all trial runners to finish
        running before returning.

        Parameters
        ----------
        wait_all : bool
            If True, wait for all trial runners to finish. If False, wait for
            :py:attr:`~.TrialRunner.idle_worker_scheduling_batch_size` number of
            idle trial runners to finish. Default is False.

        Notes
        -----
        This is called in the parent process, so it must not block the main
        thread.
        """
        assert not is_child_process(), "This should be called in the parent process."
        if wait_all:
            # Wait for all trial runners to finish.
            _LOG.info("Waiting for all trial runners to finish.")
            while self._has_running_trial_runners():
                sleep(self._polling_interval)
            assert not self._has_running_trial_runners(), "All trial runners should be idle."
        else:
            # Wait for a batch of idle trial runners to finish.
            _LOG.info(
                "Waiting for %d idle trial runners to finish.",
                self._idle_worker_scheduling_batch_size,
            )
            while self._get_idle_trial_runners_count() < self._idle_worker_scheduling_batch_size:
                sleep(self._polling_interval)
            assert self._get_idle_trial_runners_count() >= self._idle_worker_scheduling_batch_size

    @staticmethod
    def teardown_trial_runner(trial_runner: TrialRunner) -> TrialRunnerResult:
        """
        Tear down a specific :py:class:`.TrialRunner` (and its
        :py:class:`~mlos_bench.environments.base_environment.Environment`) in a
        :py:class:`.Pool` worker.

        Parameters
        ----------
        trial_runner : TrialRunner
            The :py:class:`.TrialRunner` to tear down.

        Returns
        -------
        TrialRunnerResult
            The result of the teardown operation, including the trial_runner_id
            and the result of the teardown operation.

        Notes
        -----
        This is called in the Pool worker process, so it must receive arguments
        that are picklable.
        To keep life simple we pass the entire TrialRunner object, which should
        **not** be have entered its context (else it may have non-picklable
        state), and make this a static method of the class to avoid needing to
        pass the :py:class:`~.ParallelScheduler` instance.
        Upon completion a callback is used to update the status of the
        TrialRunner in the ParallelScheduler with the value in the
        TrialRunnerResult.
        """
        assert is_child_process(), "This should be called in a Pool worker."
        with trial_runner:
            return TrialRunnerResult(
                trial_runner_id=trial_runner.trial_runner_id,
                results=trial_runner.teardown(),
            )

    def _teardown_trial_runner_finished_callback(self, result: TrialRunnerResult) -> None:
        """Callback to be called when a TrialRunner is finished with teardown."""
        assert not is_child_process(), "This should be called in the parent process."
        trial_runner_id = result.trial_runner_id
        assert (
            trial_runner_id in self._trial_runners_status
        ), f"Unexpected TrialRunner {trial_runner_id}."
        assert (
            self._trial_runners_status[trial_runner_id] is not None
        ), f"TrialRunner {trial_runner_id} should have been running."
        self._trial_runners_status[result.trial_runner_id] = None
        # Nothing to do with the result.

    @staticmethod
    def _teardown_trial_runner_failed_closure(trial_runner_id: int) -> Callable[[Any], None]:
        """Callback to be called when a TrialRunner failed running teardown."""

        def _teardown_trial_runner_failed(obj: Any) -> None:
            """Callback to be called when a TrialRunner failed running teardown."""
            assert not is_child_process(), "This should be called in the parent process."
            # TODO: improve error handling here
            _LOG.error("TrialRunner %d failed to run teardown: %s", trial_runner_id, obj)
            raise RuntimeError(f"TrialRunner {trial_runner_id} failed to run teardown: {obj}")

        return _teardown_trial_runner_failed

    def teardown(self) -> None:
        assert not is_child_process(), "This should be called in the parent process."
        assert self._pool is not None
        assert self._in_context
        assert not self._has_running_trial_runners(), "All trial runners should be idle."
        if self._do_teardown:
            # Call teardown on each TrialRunner in the pool in parallel.
            for trial_runner_id, trial_runner in self._trial_runners.items():
                assert (
                    self._trial_runners_status[trial_runner_id] is None
                ), f"TrialRunner {trial_runner} is still active."
                self._trial_runners_status[trial_runner_id] = self._pool.apply_async(
                    # Call the teardown function in the child process targeting
                    # a particular trial_runner.
                    self.teardown_trial_runner,
                    args=(trial_runner,),
                    callback=self._teardown_trial_runner_finished_callback,
                    error_callback=self._teardown_trial_runner_failed_closure(trial_runner_id),
                )

            # Wait for all trial runners to finish.
            while self._has_running_trial_runners():
                sleep(self._polling_interval)
        assert not self._has_running_trial_runners(), "All trial runners should be idle."

    def assign_trial_runners(self, trials: Iterable[Storage.Trial]) -> None:
        """
        Assign :py:class:`~.Storage.Trial`s to the first available and idle
        :py:class:`.TrialRunner`.

        Parameters
        ----------
        trials : Iterable[Storage.Trial]
        """
        assert self._in_context
        assert self.experiment is not None
        assert not is_child_process(), "This should be called in the parent process."

        scheduleable_trials: list[Storage.Trial] = list(
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
        for trial, runner_id in zip(scheduleable_trials, idle_runner_ids):
            trial.set_trial_runner(runner_id)
