#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for LocalEnv benchmark environment.
"""
from datetime import datetime, timedelta

from mlos_bench.environments.local.local_env import LocalEnv
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_local_env(tunable_groups: TunableGroups) -> None:
    """
    Produce benchmark and telemetry data in a local script and read it.
    """
    ts1 = datetime.utcnow()
    ts1 -= timedelta(microseconds=ts1.microsecond)  # Round to a second
    ts2 = ts1 + timedelta(minutes=1)

    time_str1 = ts1.strftime("%Y-%m-%d %H:%M:%S")
    time_str2 = ts2.strftime("%Y-%m-%d %H:%M:%S")

    local_env = LocalEnv(
        name="Test Local Env",
        config={
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
        },
        tunables=tunable_groups,
        service=LocalExecService(parent=ConfigPersistenceService()),
    )

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


def test_local_env_no_header(tunable_groups: TunableGroups) -> None:
    """
    Read the telemetry data with no header.
    """
    ts1 = datetime.utcnow()
    ts1 -= timedelta(microseconds=ts1.microsecond)  # Round to a second
    ts2 = ts1 + timedelta(minutes=1)

    time_str1 = ts1.strftime("%Y-%m-%d %H:%M:%S")
    time_str2 = ts2.strftime("%Y-%m-%d %H:%M:%S")

    local_env = LocalEnv(
        name="Test Local Env",
        config={
            "run": [
                f"echo {time_str1},cpu_load,0.65 > telemetry.csv",
                f"echo {time_str1},mem_usage,10240 >> telemetry.csv",
                f"echo {time_str2},cpu_load,0.8 >> telemetry.csv",
                f"echo {time_str2},mem_usage,20480 >> telemetry.csv",
            ],
            "read_telemetry_file": "telemetry.csv",
        },
        service=LocalExecService(parent=ConfigPersistenceService()),
    )

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


def test_local_env_wrong_results(tunable_groups: TunableGroups) -> None:
    """
    Fail if the results are not in the expected format.
    """
    local_env = LocalEnv(
        name="Test Local Env",
        config={
            "run": [
                # No header
                "echo 'latency,10' > output.csv",
                "echo 'throughput,66' >> output.csv",
                "echo 'score,0.9' >> output.csv",
            ],
            "read_results_file": "output.csv",
        },
        service=LocalExecService(parent=ConfigPersistenceService()),
    )
    with local_env as env_context:
        assert env_context.setup(tunable_groups)
        (_status, _data) = env_context.run()


def test_local_env_wide(tunable_groups: TunableGroups) -> None:
    """
    Produce benchmark data in wide format and read it.
    """
    local_env = LocalEnv(
        name="Test Local Env",
        config={
            "run": [
                "echo 'latency,throughput,score' > output.csv",
                "echo '10,66,0.9' >> output.csv",
            ],
            "read_results_file": "output.csv",
        },
        tunables=tunable_groups,
        service=LocalExecService(parent=ConfigPersistenceService()),
    )
    with local_env as env_context:
        assert env_context.setup(tunable_groups)
        (status, data) = env_context.run()
        assert status.is_succeeded()
        assert data == {
            "latency": 10.0,
            "throughput": 66.0,
            "score": 0.9,
        }
