#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
    A simple single-threaded synchronous optimization loop implementation.
"""

import logging

from mlos_bench.schedulers.base_scheduler import Scheduler

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

        while self.optimizer.not_converged():
            _LOG.info("Optimization loop: %s Last trial ID: %d",
                      "Warm-up" if is_warm_up else "Run", last_trial_id)
            self._run_schedule(is_warm_up)
            last_trial_id = self._get_optimizer_suggestions(last_trial_id, is_warm_up)
            is_warm_up = False

        self._teardown()
