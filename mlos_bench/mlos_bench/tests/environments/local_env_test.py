#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for LocalEnv benchmark environment.
"""
from datetime import datetime, timedelta

import numpy as np

from mlos_bench.environments.local.local_env import LocalEnv
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_local_env_vars(tunable_groups: TunableGroups) -> None:
    """
    Check that LocalEnv can set shell environment variables.
    """
    local_env = LocalEnv(
        name="Test Local Env",
        config={
            "const_args": {
                "const_arg": 111,  # Passed into "shell_env_params"
                "other_arg": 222,  # NOT passed into "shell_env_params"
            },
            "tunable_params": ["kernel"],
            "shell_env_params": [
                "const_arg",                # From "const_arg"
                "kernel_sched_latency_ns",  # From "tunable_params"
            ],
            "run": [
                "echo const_arg,other_arg,unknown_arg,kernel_sched_latency_ns > output.csv",
                "echo $const_arg,$other_arg,$unknown_arg,$kernel_sched_latency_ns >> output.csv",
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
        assert data is not None
        assert data["const_arg"] == 111.0                       # From "const_args"
        assert np.isnan(data["other_arg"])                      # Was not included in "shell_env_params"
        assert np.isnan(data["unknown_arg"])                    # Unknown/undefined variable
        assert data["kernel_sched_latency_ns"] == 2000000.0     # From "tunable_params"


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


def test_local_env_wrong_format(tunable_groups: TunableGroups) -> None:
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
        (status, data) = env_context.run()
        assert status.is_failed()
        assert data is None


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
