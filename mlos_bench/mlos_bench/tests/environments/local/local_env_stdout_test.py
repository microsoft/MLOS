#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for extracting data from LocalEnv stdout.
"""

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.tests.environments.local import create_local_env, check_env_success


def test_local_env_stdout(tunable_groups: TunableGroups) -> None:
    """
    Print benchmark results to stdout and capture them in the LocalEnv.
    """
    local_env = create_local_env(tunable_groups, {
        "run": [
            "echo 'Benchmark results:'",  # This line should be ignored
            "echo 'latency,111'",
            "echo 'throughput,222'",
            "echo 'score,0.999'",
        ],
        "results_stdout_pattern": r"(\w+),([0-9.]+)",
    })

    check_env_success(
        local_env, tunable_groups,
        expected_results={
            "latency": 111.0,
            "throughput": 222.0,
            "score": 0.999,
        },
        expected_telemetry=[],
    )


def test_local_env_file_stdout(tunable_groups: TunableGroups) -> None:
    """
    Print benchmark results to *BOTH* stdout and a file and extract the results from both.
    """
    local_env = create_local_env(tunable_groups, {
        "run": [
            "echo 'latency,111'",
            "echo 'throughput,222'",
            "echo 'score,0.999'",
            "echo '-------------------'",  # Should be ignored
            "echo 'metric,value' > output.csv",
            "echo 'extra1,333' >> output.csv",
            "echo 'extra2,444' >> output.csv",
        ],
        "results_stdout_pattern": r"(\w+),([0-9.]+)",
        "read_results_file": "output.csv",
    })

    check_env_success(
        local_env, tunable_groups,
        expected_results={
            "latency": 111.0,
            "throughput": 222.0,
            "score": 0.999,
            "extra1": 333.0,
            "extra2": 444.0,
        },
        expected_telemetry=[],
    )
