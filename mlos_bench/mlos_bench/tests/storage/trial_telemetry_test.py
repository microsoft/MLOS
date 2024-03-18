#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for saving and restoring the telemetry data.
"""
from datetime import datetime, timedelta, tzinfo, UTC
from typing import Any, List, Optional, Tuple
from zoneinfo import ZoneInfo

import pytest
from pytest_lazy_fixtures.lazy_fixture import lf as lazy_fixture

from mlos_bench.environments.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.storage.base_storage import Storage
from mlos_bench.util import nullable

# pylint: disable=redefined-outer-name


def zoned_telemetry_data(zone_info: Optional[tzinfo]) -> List[Tuple[datetime, str, Any]]:
    """
    Mock telemetry data for the trial.

    Returns
    -------
    List[Tuple[datetime, str, str]]
        A list of (timestamp, metric_id, metric_value)
    """
    timestamp1 = datetime.now(zone_info)
    timestamp2 = timestamp1 + timedelta(seconds=1)
    return sorted([
        (timestamp1, "cpu_load", 10.1),
        (timestamp1, "memory", 20),
        (timestamp1, "setup", "prod"),
        (timestamp2, "cpu_load", 30.1),
        (timestamp2, "memory", 40),
        (timestamp2, "setup", "prod"),
    ])


@pytest.fixture
def telemetry_data_implicit_local() -> List[Tuple[datetime, str, Any]]:
    """Telemetry data with implicit (i.e., missing) local timezone info."""
    return zoned_telemetry_data(zone_info=None)


@pytest.fixture
def telemetry_data_utc() -> List[Tuple[datetime, str, Any]]:
    """Telemetry data with explicit UTC timezone info."""
    return zoned_telemetry_data(zone_info=UTC)


@pytest.fixture
def telemetry_data_explicit() -> List[Tuple[datetime, str, Any]]:
    """Telemetry data with explicit UTC timezone info."""
    zone_info = ZoneInfo("America/Chicago")
    assert zone_info.utcoffset(datetime.now(UTC)) != timedelta(hours=0)
    return zoned_telemetry_data(zone_info)


ZONE_INFO: List[Optional[tzinfo]] = [UTC, ZoneInfo("America/Chicago"), None]


def _telemetry_str(data: List[Tuple[datetime, str, Any]]
                   ) -> List[Tuple[datetime, str, Optional[str]]]:
    """
    Convert telemetry values to strings.
    """
    # All retrieved timestamps should have been converted to UTC.
    return [(ts.astimezone(UTC), key, nullable(str, val)) for (ts, key, val) in data]


@pytest.mark.parametrize(("telemetry_data"), [
    (lazy_fixture("telemetry_data_implicit_local")),
    (lazy_fixture("telemetry_data_utc")),
    (lazy_fixture("telemetry_data_explicit")),
])
@pytest.mark.parametrize(("origin_zone_info"), ZONE_INFO)
def test_update_telemetry(storage: Storage,
                          exp_storage: Storage.Experiment,
                          tunable_groups: TunableGroups,
                          telemetry_data: List[Tuple[datetime, str, Any]],
                          origin_zone_info: Optional[tzinfo]) -> None:
    """
    Make sure update_telemetry() and load_telemetry() methods work.
    """
    trial = exp_storage.new_trial(tunable_groups)
    assert exp_storage.load_telemetry(trial.trial_id) == []

    trial.update_telemetry(Status.RUNNING, datetime.now(origin_zone_info), telemetry_data)
    assert exp_storage.load_telemetry(trial.trial_id) == _telemetry_str(telemetry_data)

    # Also check that the TrialData telemetry looks right.
    trial_data = storage.experiments[exp_storage.experiment_id].trials[trial.trial_id]
    trial_telemetry_df = trial_data.telemetry_df
    trial_telemetry_data = [tuple(r) for r in trial_telemetry_df.to_numpy()]
    assert _telemetry_str(trial_telemetry_data) == _telemetry_str(telemetry_data)


@pytest.mark.parametrize(("telemetry_data"), [
    (lazy_fixture("telemetry_data_implicit_local")),
    (lazy_fixture("telemetry_data_utc")),
    (lazy_fixture("telemetry_data_explicit")),
])
@pytest.mark.parametrize(("origin_zone_info"), ZONE_INFO)
def test_update_telemetry_twice(exp_storage: Storage.Experiment,
                                tunable_groups: TunableGroups,
                                telemetry_data: List[Tuple[datetime, str, Any]],
                                origin_zone_info: Optional[tzinfo]) -> None:
    """
    Make sure update_telemetry() call is idempotent.
    """
    trial = exp_storage.new_trial(tunable_groups)
    timestamp = datetime.now(origin_zone_info)
    trial.update_telemetry(Status.RUNNING, timestamp, telemetry_data)
    trial.update_telemetry(Status.RUNNING, timestamp, telemetry_data)
    trial.update_telemetry(Status.RUNNING, timestamp, telemetry_data)
    assert exp_storage.load_telemetry(trial.trial_id) == _telemetry_str(telemetry_data)
