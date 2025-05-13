#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A mock scheduler that returns predefined status and score for specific trial IDs.
"""

import logging

from datetime import datetime
from collections.abc import Iterable
from typing import Any

from pytz import UTC

from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.storage.base_storage import Storage
from mlos_bench.schedulers.base_scheduler import Optimizer
from mlos_bench.schedulers.trial_runner import TrialRunner

_LOG = logging.getLogger(__name__)


class MockScheduler(Scheduler):
    """
    A mock scheduler that returns predefined status and score for specific trial IDs.
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
    ) -> None:
        super().__init__(
            config=config,
            global_config=global_config,
            trial_runners=trial_runners,
            optimizer=optimizer,
            storage=storage,
            root_env_config=root_env_config,
        )
        self._mock_trial_data = config.get("mock_trial_data", [])
        self._mock_trial_data = {
            trial_info["trial_id"]: trial_info
            for trial_info in self._mock_trial_data
        }

    def run_trial(self, trial: Storage.Trial) -> None:
        """
        Mock the execution of a trial.

        Parameters:
        ----------
        trial : Storage.Trial
            The trial to be executed.
        """
        trial_id = trial.trial_id
        if trial_id not in self._mock_trial_data:
            raise ValueError(f"Trial ID {trial_id} not found in mock trial data.")

        trial_info = self._mock_trial_data[trial_id]
        _LOG.info("Running trial %d: %s", trial_id, trial_info)
        trial.update(trial_info["status"], datetime.now(UTC), trial_info.get("score"))
