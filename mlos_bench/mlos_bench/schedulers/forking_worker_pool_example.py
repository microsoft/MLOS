#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Simple parallel trial scheduler and optimization loop implementation stub code."""
import json
import random
from multiprocessing.pool import AsyncResult, Pool
from time import sleep
from typing import Any


class TrialRunner:  # pylint: disable=too-few-public-methods
    """Stub TrialRunner."""

    def __init__(self, runner_id: int):
        self.runner_id = runner_id

    def run_trial(self, iteration: int, suggestion: int) -> dict[str, int | float]:
        """Stub run_trial."""
        # In the real system we'd run the Trial on the Environment and whatnot.
        sleep_time = random.uniform(0, 1) + 0.01
        print(
            (
                f"Trial {iteration} is running on {self.runner_id} "
                f"with suggestion {suggestion} with sleep time {sleep_time}"
            ),
            flush=True,
        )
        # Wait a moment to simulate the time it takes to run the trial.
        sleep(sleep_time)
        print(f"Trial {iteration} on {self.runner_id} is done.", flush=True)
        return {
            "runner_id": self.runner_id,
            "iteration": iteration,
            "suggestion": suggestion,
            "sleep_time": sleep_time,
        }


class ParallelTrialScheduler:
    """Stub ParallelTrialScheduler."""

    def __init__(self, num_trial_runners: int, max_iterations: int):
        self._max_iterations = max_iterations
        self._trial_runners = [TrialRunner(i) for i in range(num_trial_runners)]

        # Track the current status of a TrialRunner.
        # In a real system we might need to track which TrialRunner is busy in
        # the backend Storage in case of failures of the main process or else
        # just treat their state as idempotent such that we could resume and
        # check on their status at any time.
        # That would also require a deterministic scheduling algorithm so that
        # we restart the same Trial on the same TrialRunner rather than picking
        # a new one.
        self._trial_runners_status: dict[int, AsyncResult | None] = {
            runner.runner_id: None for runner in self._trial_runners
        }

        # Simple trial schedule: maps a trial id to a TrialRunner.
        # In the real system we'd store everything in the Storage backend.
        self._trial_schedule: dict[int, tuple[int, int]] = {}
        self._current_runner_id = 0

        # Store all the results in a dictionary.
        # In the real system we'd submit them to the Storage and the Optimizer.
        self._results: dict[int, dict[str, int | float]] = {}

    def get_last_trial_id(self) -> int:
        """Very simple method of tracking the last trial id assigned."""
        return max(list(self._results.keys()) + list(self._trial_schedule.keys()), default=-1)

    def is_done_scheduling(self) -> bool:
        """Check if the scheduler loop is done."""
        # This is a simple stopping condition to check and see if we've
        # scheduled enough trials.
        return self.get_last_trial_id() + 1 >= self._max_iterations

    def is_done_running(self) -> bool:
        """Check if the scheduler run loop is done."""
        # This is a simple stopping condition to check and see if we've
        # run all the trials.
        return len(self._results) >= self._max_iterations

    def assign_trial_runner(self, trial_id: int, suggestion: int) -> None:
        """Stub assign_trial_runner."""
        # In a real system we'd have a more sophisticated way of assigning
        # trials to TrialRunners.
        # Here we just round-robin the suggestions to the available TrialRunners.
        next_runner_id = self._current_runner_id
        self._current_runner_id = (self._current_runner_id + 1) % len(self._trial_runners)
        self._trial_schedule[trial_id] = (next_runner_id, suggestion)
        print(
            f"Assigned trial {trial_id} to runner {next_runner_id} with suggestion {suggestion}",
            flush=True,
        )

    def schedule_new_trials(self, num_new_trials: int = 1) -> None:
        """Stub schedule_new_trial(s)."""

        # Accept more than one new suggestion at a time to simulate a real
        # system that might be doing multi-objective pareto frontier
        # optimization.

        while num_new_trials > 0 and not self.is_done_scheduling():
            # Generate one (or more) new suggestion(s).
            # In the real system we'd get these from the Optimizer.
            suggestion = random.randint(0, 100)

            # Note: it might be also be the case that we want to repeat that
            # suggestion multiple times on different TrialRunners.

            # Schedule it to a TrialRunner.
            next_trial_id = self.get_last_trial_id() + 1
            self.assign_trial_runner(next_trial_id, suggestion)
            num_new_trials -= 1

    def _run_trial_failed_callback(self, obj: Any) -> None:  # pylint: disable=no-self-use
        """Stub callback to run when run_trial fails in pool process."""
        raise RuntimeError(f"Trial failed: {obj}")

    def _run_trial_finished_callback(self, result: dict[str, int | float]) -> None:
        """Stub callback to run when run_trial finishes in pool process."""

        # Store the result of the trial.
        trial_id = result["iteration"]
        assert isinstance(trial_id, int)
        self._results[trial_id] = result

        # Remove it from the schedule.
        self._trial_schedule.pop(trial_id)

        # And mark the TrialRunner as available.
        runner_id = result["runner_id"]
        assert isinstance(runner_id, int)
        trial_runner_status = self._trial_runners_status.get(runner_id)
        assert isinstance(trial_runner_status, AsyncResult)
        # assert trial_runner_status.ready()
        self._trial_runners_status[runner_id] = None

        print(f"Trial {trial_id} on {runner_id} callback is done.", flush=True)

        # Schedule more trials.
        # Note: this would schedule additional trials everytime one completes.
        # An alternative option would be to batch them up and schedule several
        # after a few complete.
        # The tradeoffs being model retraining time vs. waiting on straggler
        # workers vs. optimizer new suggestion accuracy.
        # Moreover, we need to handle the edge case and include scheduling in
        # the loop anyways, so it's probably better to just leave it all there.
        # self.schedule_new_trials(num_new_trials=1)

    def get_idle_trial_runners_count(self) -> int:
        """Stub get_idle_trial_runners_count."""
        return len([x for x in self._trial_runners_status.values() if x is None])

    def start_optimization_loop(self) -> None:
        """Stub start_optimization_loop."""

        # Create a pool of processes to run the trials in parallel.
        with Pool(processes=len(self._trial_runners), maxtasksperchild=1) as pool:
            while not self.is_done_scheduling() or not self.is_done_running():
                # Run any existing trials that aren't currently running.
                # Do this first in case we're resuming from a previous run
                # (e.g., the real system will have remembered which Trials were
                # in progress by reloading them from the Storage backend).

                # Avoid modifying the dictionary while iterating over it.
                trial_schedule = self._trial_schedule.copy()
                for trial_id, (runner_id, suggestion) in trial_schedule.items():
                    # Skip trials that are already running on their assigned TrialRunner.
                    if self._trial_runners_status[runner_id] is not None:
                        continue
                    # Else, start the Trial on the given TrialRunner in the background.
                    self._trial_runners_status[runner_id] = pool.apply_async(
                        TrialRunner(runner_id).run_trial,
                        args=(trial_id, suggestion),
                        callback=self._run_trial_finished_callback,
                        error_callback=self._run_trial_failed_callback,
                    )
                # Now all the available TrialRunners that had work to do should be running.

                # Wait a moment to check if we have any idle TrialRunners.
                # This also allows us a chance to collect multiple results from
                # the pool before suggesting new ones.
                while len(self._trial_schedule) > 0 and self.get_idle_trial_runners_count() == 0:
                    # Make the polling interval here configurable.
                    sleep(0.5)

                # Schedule more trials if we can.
                self.schedule_new_trials(num_new_trials=self.get_idle_trial_runners_count() or 1)

            # Should be all done starting new trials.
            print("Closing the pool.", flush=True)
            pool.close()

            print("Waiting for all trials to finish.", flush=True)
            # FIXME: This sometimes hangs. Not sure why yet.
            pool.join()

        print("Optimization loop is done.", flush=True)
        print("results: " + json.dumps(self._results, indent=2))
        print("trial_schedule: " + json.dumps(self._trial_schedule, indent=2))
        print("trial_runner_status: " + json.dumps(self._trial_runners_status, indent=2))
        assert len(self._results) == self._max_iterations, "Unexpected number of trials run."
        assert not self._trial_schedule, "Some scheduled trials were not started."
        assert all(
            x is None for x in self._trial_runners_status.values()
        ), "Some TrialRunners are still running."


def main():
    """Main function."""
    print("Starting ParallelTrialScheduler.", flush=True)
    scheduler = ParallelTrialScheduler(num_trial_runners=4, max_iterations=15)
    scheduler.start_optimization_loop()


if __name__ == "__main__":
    main()
