# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
MockTrialRunner for testing :py:class:`mlos_bench.schedulers.Scheduler` logic
with mock trial data.

This class is intended for use in unit tests and allows for deterministic trial
execution by returning pre-specified results from the ``global_config``.

Example
-------
Setup mock trial data in the global_config.

>>> mock_trial_data = {
...     1: {
...         "trial_id": 1,
...         "status": "SUCCEEDED",
...         "metrics": {
...             "score": 42.0,
...             "color": "red"
...         },
...         # Optional sleep time in seconds
...         "sleep": 0.1
...     },
...     # Add more trials as needed.
... }

Normally, this would be part of the global_config passed to the scheduler.
>>> global_config = {
...     "mock_trial_data": mock_trial_data,
...     # Other global config parameters...
... }

>>> runner = MockTrialRunner(0, env)
>>> status, timestamp, metrics = runner.run_trial(trial, global_config)
>>> print(status, metrics)
Status.SUCCEEDED {'score': 42.0, 'color': 'red'}
"""
import time
from datetime import datetime
from typing import Any

from mlos_bench.schedulers.trial_runner import TrialRunner
from mlos_bench.storage.base_storage import Storage
from mlos_bench.environments.status import Status
from mlos_bench.tunables.tunable_types import TunableValue


class MockTrialRunner(TrialRunner):
    """
    Mock implementation of TrialRunner for testing.

    This class overrides the run_trial method to return mock results
    from the global_config["mock_trial_data"] dict, keyed by trial_id.

    """

    def run_trial(
        self,
        trial: Storage.Trial,
        global_config: dict[str, Any] | None = None,
    ) -> tuple[Status, datetime, dict[str, TunableValue] | None]:
        """
        Run a mock trial using data from global_config["mock_trial_data"].

        Parameters
        ----------
        trial : Storage.Trial
            The trial object, must have a trial_id attribute.
        global_config : dict
            Global configuration, must contain "mock_trial_data".

        Returns
        -------
        (status, timestamp, metrics) : (Status, datetime, dict[str, TunableValue] | None)
            Status, timestamp, and metrics for the mock trial.
        """
        assert global_config is not None, "global_config must be provided."
        mock_data = global_config.get("mock_trial_data", {})
        trial_id = getattr(trial, "trial_id", None)
        assert trial_id in mock_data, f"No mock data for trial_id {trial_id}"
        data = mock_data[trial_id]
        sleep_time = data.get("sleep", 0.01)
        time.sleep(sleep_time)
        status = Status[data.get("status", "SUCCEEDED")]
        metrics = data.get("metrics", {})
        timestamp = datetime.now()
        return status, timestamp, metrics
