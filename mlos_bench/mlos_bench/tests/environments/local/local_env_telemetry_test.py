#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for telemetry and status of LocalEnv benchmark environment.
"""
from datetime import datetime, timedelta, UTC
import pytz

import pytest

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.tests.environments import check_env_success, check_env_fail_telemetry
from mlos_bench.tests.environments.local import create_local_env


def test_local_env_telemetry(tunable_groups: TunableGroups) -> None:
    """
    Produce benchmark and telemetry data in a local script and read it.
    """
    ts1 = datetime.now(UTC).astimezone(pytz.UTC)
    ts1 -= timedelta(microseconds=ts1.microsecond)  # Round to a second
    ts2 = ts1 + timedelta(minutes=1)

    time_str1 = ts1.strftime("%Y-%m-%d %H:%M:%S %z")
    time_str2 = ts2.strftime("%Y-%m-%d %H:%M:%S %z")

    local_env = create_local_env(tunable_groups, {
        "run": [
            "echo 'metric,value' > output.csv",
            "echo 'latency,4.1' >> output.csv",
            "echo 'throughput,512' >> output.csv",
            "echo 'score,0.95' >> output.csv",
            "echo '-------------------'",  # This output does not go anywhere
            "echo 'timestamp,metric,value' > telemetry.csv",
            f"echo {time_str1},cpu_load,0.65 >> telemetry.csv",
            f"echo {time_str1},mem_usage,10240 >> telemetry.csv",
            f"echo {time_str2},cpu_load,0.8 >> telemetry.csv",
            f"echo {time_str2},mem_usage,20480 >> telemetry.csv",
        ],
        "read_results_file": "output.csv",
        "read_telemetry_file": "telemetry.csv",
    })

    check_env_success(
        local_env, tunable_groups,
        expected_results={
            "latency": 4.1,
            "throughput": 512.0,
            "score": 0.95,
        },
        expected_telemetry=[
            (ts1, "cpu_load", 0.65),
            (ts1, "mem_usage", 10240.0),
            (ts2, "cpu_load", 0.8),
            (ts2, "mem_usage", 20480.0),
        ],
    )


def test_local_env_telemetry_no_header(tunable_groups: TunableGroups) -> None:
    """
    Read the telemetry data with no header.
    """
    ts1 = datetime.now(UTC).astimezone(pytz.UTC)
    ts1 -= timedelta(microseconds=ts1.microsecond)  # Round to a second
    ts2 = ts1 + timedelta(minutes=1)

    time_str1 = ts1.strftime("%Y-%m-%d %H:%M:%S %z")
    time_str2 = ts2.strftime("%Y-%m-%d %H:%M:%S %z")

    local_env = create_local_env(tunable_groups, {
        "run": [
            f"echo {time_str1},cpu_load,0.65 > telemetry.csv",
            f"echo {time_str1},mem_usage,10240 >> telemetry.csv",
            f"echo {time_str2},cpu_load,0.8 >> telemetry.csv",
            f"echo {time_str2},mem_usage,20480 >> telemetry.csv",
        ],
        "read_telemetry_file": "telemetry.csv",
    })

    check_env_success(
        local_env, tunable_groups,
        expected_results={},
        expected_telemetry=[
            (ts1, "cpu_load", 0.65),
            (ts1, "mem_usage", 10240.0),
            (ts2, "cpu_load", 0.8),
            (ts2, "mem_usage", 20480.0),
        ],
    )


@pytest.mark.filterwarnings("ignore:.*(Could not infer format, so each element will be parsed individually, falling back to `dateutil`).*:UserWarning::0")  # pylint: disable=line-too-long # noqa
def test_local_env_telemetry_wrong_header(tunable_groups: TunableGroups) -> None:
    """
    Read the telemetry data with incorrect header.
    """
    ts1 = datetime.now(UTC).astimezone(pytz.UTC)
    ts1 -= timedelta(microseconds=ts1.microsecond)  # Round to a second
    ts2 = ts1 + timedelta(minutes=1)

    time_str1 = ts1.strftime("%Y-%m-%d %H:%M:%S %z")
    time_str2 = ts2.strftime("%Y-%m-%d %H:%M:%S %z")

    local_env = create_local_env(tunable_groups, {
        "run": [
            # Error: the data is correct, but the header has unexpected column names
            "echo 'ts,metric_name,metric_value' > telemetry.csv",
            f"echo {time_str1},cpu_load,0.65 >> telemetry.csv",
            f"echo {time_str1},mem_usage,10240 >> telemetry.csv",
            f"echo {time_str2},cpu_load,0.8 >> telemetry.csv",
            f"echo {time_str2},mem_usage,20480 >> telemetry.csv",
        ],
        "read_telemetry_file": "telemetry.csv",
    })

    check_env_fail_telemetry(local_env, tunable_groups)


def test_local_env_telemetry_invalid(tunable_groups: TunableGroups) -> None:
    """
    Fail when the telemetry data has wrong format.
    """
    ts1 = datetime.now(UTC).astimezone(pytz.UTC)
    ts1 -= timedelta(microseconds=ts1.microsecond)  # Round to a second
    ts2 = ts1 + timedelta(minutes=1)

    time_str1 = ts1.strftime("%Y-%m-%d %H:%M:%S %z")
    time_str2 = ts2.strftime("%Y-%m-%d %H:%M:%S %z")

    local_env = create_local_env(tunable_groups, {
        "run": [
            # Error: too many columns
            f"echo {time_str1},EXTRA,cpu_load,0.65 > telemetry.csv",
            f"echo {time_str1},EXTRA,mem_usage,10240 >> telemetry.csv",
            f"echo {time_str2},EXTRA,cpu_load,0.8 >> telemetry.csv",
            f"echo {time_str2},EXTRA,mem_usage,20480 >> telemetry.csv",
        ],
        "read_telemetry_file": "telemetry.csv",
    })

    check_env_fail_telemetry(local_env, tunable_groups)


def test_local_env_telemetry_invalid_ts(tunable_groups: TunableGroups) -> None:
    """
    Fail when the telemetry data has wrong format.
    """
    local_env = create_local_env(tunable_groups, {
        "run": [
            # Error: field 1 must be a timestamp
            "echo 1,cpu_load,0.65 > telemetry.csv",
            "echo 2,mem_usage,10240 >> telemetry.csv",
            "echo 3,cpu_load,0.8 >> telemetry.csv",
            "echo 4,mem_usage,20480 >> telemetry.csv",
        ],
        "read_telemetry_file": "telemetry.csv",
    })

    check_env_fail_telemetry(local_env, tunable_groups)
