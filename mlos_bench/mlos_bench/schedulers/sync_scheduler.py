#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A simple single-threaded synchronous optimization loop implementation."""

import logging

from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.storage.base_storage import Storage

_LOG = logging.getLogger(__name__)


class SyncScheduler(Scheduler):
    """A simple single-threaded synchronous optimization loop implementation."""

    def run_trial(self, trial: Storage.Trial) -> None:
        """
        Set up and run a single :py:class:`~.Storage.Trial` on its
        :py:class:`~.TrialRunner`.

        Save the results in the storage.
        """
        super().run_trial(trial)
        # In the sync scheduler we run each trial on its own TrialRunner in sequence.
        trial_runner = self.get_trial_runner(trial)
        with trial_runner:
            trial_runner.run_trial(trial, self.global_config)
            _LOG.info("QUEUE: Finished trial: %s on %s", trial, trial_runner)
