#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for the composition of several LocalEnv benchmark environments.
"""
from datetime import datetime, timedelta

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.tests.environments.local import create_composite_local_env, check_env_success


def test_composite_env(tunable_groups: TunableGroups) -> None:
    """
    Produce benchmark and telemetry data in TWO local environments
    and combine the results.
    """
    ts1 = datetime.utcnow()
    ts1 -= timedelta(microseconds=ts1.microsecond)  # Round to a second
    ts2 = ts1 + timedelta(minutes=1)

    time_str1 = ts1.strftime("%Y-%m-%d %H:%M:%S")
    time_str2 = ts2.strftime("%Y-%m-%d %H:%M:%S")

    env = create_composite_local_env(tunable_groups, [
        {
            "run": [
                "echo 'metric,value' > output.csv",
                "echo 'latency,4.2' >> output.csv",
                "echo '-------------------'",  # This output does not go anywhere
                "echo 'timestamp,metric,value' > telemetry.csv",
                f"echo {time_str1},cpu_load,0.64 >> telemetry.csv",
                f"echo {time_str1},mem_usage,5120 >> telemetry.csv",
            ],
            "read_results_file": "output.csv",
            "read_telemetry_file": "telemetry.csv",
        },
        {
            "run": [
                "echo 'metric,value' > output.csv",
                "echo 'throughput,768' >> output.csv",
                "echo 'score,0.97' >> output.csv",
                "echo '-------------------'",  # This output does not go anywhere
                "echo 'timestamp,metric,value' > telemetry.csv",
                f"echo {time_str2},cpu_load,0.79 >> telemetry.csv",
                f"echo {time_str2},mem_usage,40960 >> telemetry.csv",
            ],
            "read_results_file": "output.csv",
            "read_telemetry_file": "telemetry.csv",
        }
    ])

    check_env_success(
        env, tunable_groups,
        expected_results={
            "latency": 4.2,
            "throughput": 768.0,
            "score": 0.97,
        },
        expected_telemetry=[
            (ts1, "cpu_load", 0.64),
            (ts1, "mem_usage", 5120.0),
            (ts2, "cpu_load", 0.79),
            (ts2, "mem_usage", 40960.0),
        ],
    )
