#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for the storage subsystem.
"""
from datetime import datetime, timedelta
from typing import List, Tuple

import pytest

from mlos_bench.environments.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.storage.base_storage import Storage

# pylint: disable=redefined-outer-name


@pytest.fixture
def telemetry_data() -> List[Tuple[datetime, str, str]]:
    """
    Mock telemetry data for the trial.

    Returns
    -------
    List[Tuple[datetime, str, str]]
        A list of (timestamp, metric_id, metric_value)
    """
    timestamp1 = datetime.now()
    timestamp2 = timestamp1 + timedelta(seconds=1)
    return [
        (timestamp1, "cpu_load", "10"),
        (timestamp1, "memory", "20"),
        (timestamp2, "cpu_load", "30"),
        (timestamp2, "memory", "40"),
    ]


def test_update_telemetry_twice(exp_storage_memory_sql: Storage.Experiment,
                                tunable_groups: TunableGroups,
                                telemetry_data: List[Tuple[datetime, str, str]]) -> None:
    """
    Make sure update_telemetry() call is idempotent.
    """
    trial = exp_storage_memory_sql.new_trial(tunable_groups)
    trial.update_telemetry(Status.RUNNING, telemetry_data)
    trial.update_telemetry(Status.RUNNING, telemetry_data)
    trial.update_telemetry(Status.RUNNING, telemetry_data)
