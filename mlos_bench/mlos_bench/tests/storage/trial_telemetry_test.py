#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for saving and restoring the telemetry data.
"""
from datetime import datetime, timedelta
from typing import Any, List, Optional, Tuple

import pytest

from mlos_bench.environments.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.storage.base_storage import Storage

# pylint: disable=redefined-outer-name


@pytest.fixture
def telemetry_data() -> List[Tuple[datetime, str, Any]]:
    """
    Mock telemetry data for the trial.

    Returns
    -------
    List[Tuple[datetime, str, str]]
        A list of (timestamp, metric_id, metric_value)
    """
    timestamp1 = datetime.utcnow()
    timestamp2 = timestamp1 + timedelta(seconds=1)
    return sorted([
        (timestamp1, "cpu_load", 10.1),
        (timestamp1, "memory", 20),
        (timestamp1, "setup", "prod"),
        (timestamp2, "cpu_load", 30.1),
        (timestamp2, "memory", 40),
        (timestamp2, "setup", "prod"),
    ])


def _telemetry_str(data: List[Tuple[datetime, str, Any]]
                   ) -> List[Tuple[datetime, str, Optional[str]]]:
    """
    Convert telemetry values to strings.
    """
    return [(ts, key, None if val is None else str(val)) for (ts, key, val) in data]


def test_update_telemetry(exp_storage_memory_sql: Storage.Experiment,
                          tunable_groups: TunableGroups,
                          telemetry_data: List[Tuple[datetime, str, Any]]) -> None:
    """
    Make sure update_telemetry() and load_telemetry() methods work.
    """
    trial = exp_storage_memory_sql.new_trial(tunable_groups)
    assert exp_storage_memory_sql.load_telemetry(trial.trial_id) == []

    trial.update_telemetry(Status.RUNNING, telemetry_data)
    assert exp_storage_memory_sql.load_telemetry(trial.trial_id) == _telemetry_str(telemetry_data)


def test_update_telemetry_twice(exp_storage_memory_sql: Storage.Experiment,
                                tunable_groups: TunableGroups,
                                telemetry_data: List[Tuple[datetime, str, Any]]) -> None:
    """
    Make sure update_telemetry() call is idempotent.
    """
    trial = exp_storage_memory_sql.new_trial(tunable_groups)
    trial.update_telemetry(Status.RUNNING, telemetry_data)
    trial.update_telemetry(Status.RUNNING, telemetry_data)
    trial.update_telemetry(Status.RUNNING, telemetry_data)
    assert exp_storage_memory_sql.load_telemetry(trial.trial_id) == _telemetry_str(telemetry_data)
