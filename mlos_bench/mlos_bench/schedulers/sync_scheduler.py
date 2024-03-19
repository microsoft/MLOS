#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A simple single-threaded synchronous optimization loop implementation.
"""

import logging
from datetime import datetime

from pytz import UTC

from mlos_bench.environments.status import Status
from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.storage.base_storage import Storage

_LOG = logging.getLogger(__name__)


class SyncScheduler(Scheduler):
    """
    A simple single-threaded synchronous optimization loop implementation.
    """

    def start(self) -> None:
        """
        Start the optimization loop.
        """
        super().start()

        last_trial_id = -1
        is_warm_up = self.optimizer.supports_preload
        if not is_warm_up:
            _LOG.warning("Skip pending trials and warm-up: %s", self.optimizer)

        while self.not_converged():
            _LOG.info("Optimization loop: %s Last trial ID: %d",
                      "Warm-up" if is_warm_up else "Run", last_trial_id)
            self._run_schedule(is_warm_up)
            last_trial_id = self._get_optimizer_suggestions(last_trial_id, is_warm_up)
            is_warm_up = False

    def run_trial(self, trial: Storage.Trial) -> None:
        """
        Set up and run a single trial. Save the results in the storage.
        """
        super().run_trial(trial)

        if not self.environment.setup(trial.tunables, trial.config(self.global_config)):
            _LOG.warning("Setup failed: %s :: %s", self.environment, trial.tunables)
            # FIXME: Use the actual timestamp from the environment.
            _LOG.info("QUEUE: Update trial results: %s :: %s", trial, Status.FAILED)
            trial.update(Status.FAILED, datetime.now(UTC))
            return

        (status, timestamp, results) = self.environment.run()  # Block and wait for the final result.
        _LOG.info("Results: %s :: %s\n%s", trial.tunables, status, results)

        # In async mode (TODO), poll the environment for status and telemetry
        # and update the storage with the intermediate results.
        (_status, _timestamp, telemetry) = self.environment.status()

        # Use the status and timestamp from `.run()` as it is the final status of the experiment.
        # TODO: Use the `.status()` output in async mode.
        trial.update_telemetry(status, timestamp, telemetry)

        trial.update(status, timestamp, results)
        _LOG.info("QUEUE: Update trial results: %s :: %s %s", trial, status, results)
