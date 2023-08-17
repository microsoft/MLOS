#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for telemetry and status of LocalEnv benchmark environment.
"""
from datetime import datetime, timedelta

import pytest

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.tests.environments.local import create_local_env


def test_local_env_telemetry(tunable_groups: TunableGroups) -> None:
    """
    Produce benchmark and telemetry data in a local script and read it.
    """
    ts1 = datetime.utcnow()
    ts1 -= timedelta(microseconds=ts1.microsecond)  # Round to a second
    ts2 = ts1 + timedelta(minutes=1)

    time_str1 = ts1.strftime("%Y-%m-%d %H:%M:%S")
    time_str2 = ts2.strftime("%Y-%m-%d %H:%M:%S")

    local_env = create_local_env(tunable_groups, {
        "run": [
            "echo 'metric,value' > output.csv",
            "echo 'latency,10' >> output.csv",
            "echo 'throughput,66' >> output.csv",
            "echo 'score,0.9' >> output.csv",
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

    with local_env as env_context:

        assert env_context.setup(tunable_groups)

        (status, data) = env_context.run()
        assert status.is_succeeded()
        assert data == {
            "latency": 10.0,
            "throughput": 66.0,
            "score": 0.9,
        }

        (status, telemetry) = env_context.status()
        assert status.is_good()
        assert telemetry == [
            (ts1, "cpu_load", 0.65),
            (ts1, "mem_usage", 10240.0),
            (ts2, "cpu_load", 0.8),
            (ts2, "mem_usage", 20480.0),
        ]


def test_local_env_telemetry_no_header(tunable_groups: TunableGroups) -> None:
    """
    Read the telemetry data with no header.
    """
    ts1 = datetime.utcnow()
    ts1 -= timedelta(microseconds=ts1.microsecond)  # Round to a second
    ts2 = ts1 + timedelta(minutes=1)

    time_str1 = ts1.strftime("%Y-%m-%d %H:%M:%S")
    time_str2 = ts2.strftime("%Y-%m-%d %H:%M:%S")

    local_env = create_local_env(tunable_groups, {
        "run": [
            f"echo {time_str1},cpu_load,0.65 > telemetry.csv",
            f"echo {time_str1},mem_usage,10240 >> telemetry.csv",
            f"echo {time_str2},cpu_load,0.8 >> telemetry.csv",
            f"echo {time_str2},mem_usage,20480 >> telemetry.csv",
        ],
        "read_telemetry_file": "telemetry.csv",
    })

    with local_env as env_context:

        assert env_context.setup(tunable_groups)
        (status, _data) = env_context.run()
        assert status.is_succeeded()

        (status, telemetry) = env_context.status()
        assert status.is_good()
        assert telemetry == [
            (ts1, "cpu_load", 0.65),
            (ts1, "mem_usage", 10240.0),
            (ts2, "cpu_load", 0.8),
            (ts2, "mem_usage", 20480.0),
        ]


def test_local_env_telemetry_wrong_header(tunable_groups: TunableGroups) -> None:
    """
    Read the telemetry data with incorrect header.
    """
    ts1 = datetime.utcnow()
    ts1 -= timedelta(microseconds=ts1.microsecond)  # Round to a second
    ts2 = ts1 + timedelta(minutes=1)

    time_str1 = ts1.strftime("%Y-%m-%d %H:%M:%S")
    time_str2 = ts2.strftime("%Y-%m-%d %H:%M:%S")

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

    with local_env as env_context:

        assert env_context.setup(tunable_groups)
        (status, _data) = env_context.run()
        assert status.is_succeeded()

        with pytest.raises(ValueError):
            env_context.status()


def test_local_env_telemetry_invalid(tunable_groups: TunableGroups) -> None:
    """
    Fail when the telemetry data has wrong format.
    """
    ts1 = datetime.utcnow()
    ts1 -= timedelta(microseconds=ts1.microsecond)  # Round to a second
    ts2 = ts1 + timedelta(minutes=1)

    time_str1 = ts1.strftime("%Y-%m-%d %H:%M:%S")
    time_str2 = ts2.strftime("%Y-%m-%d %H:%M:%S")

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

    with local_env as env_context:

        assert env_context.setup(tunable_groups)
        (status, _data) = env_context.run()
        assert status.is_succeeded()

        with pytest.raises(ValueError):
            env_context.status()


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

    with local_env as env_context:

        assert env_context.setup(tunable_groups)
        (status, _data) = env_context.run()
        assert status.is_succeeded()

        with pytest.raises(ValueError):
            env_context.status()
