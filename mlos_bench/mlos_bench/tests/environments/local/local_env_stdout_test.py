#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for extracting data from LocalEnv stdout."""

import sys

from mlos_bench.tests.environments import check_env_success
from mlos_bench.tests.environments.local import create_local_env
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_local_env_stdout(tunable_groups: TunableGroups) -> None:
    """Print benchmark results to stdout and capture them in the LocalEnv."""
    local_env = create_local_env(
        tunable_groups,
        {
            "run": [
                "echo 'Benchmark results:'",  # This line should be ignored
                "echo 'latency,111'",
                "echo 'throughput,222'",
                "echo 'score,0.999'",
                "echo 'a,0,b,1'",
            ],
            "results_stdout_pattern": r"(\w+),([0-9.]+)",
        },
    )

    check_env_success(
        local_env,
        tunable_groups,
        expected_results={
            "latency": 111.0,
            "throughput": 222.0,
            "score": 0.999,
            "a": 0,
            "b": 1,
        },
        expected_telemetry=[],
    )


def test_local_env_stdout_anchored(tunable_groups: TunableGroups) -> None:
    """Print benchmark results to stdout and capture them in the LocalEnv."""
    local_env = create_local_env(
        tunable_groups,
        {
            "run": [
                "echo 'Benchmark results:'",  # This line should be ignored
                "echo 'latency,111'",
                "echo 'throughput,222'",
                "echo 'score,0.999'",
                "echo 'a,0,b,1'",  # This line should be ignored in the case of anchored pattern
            ],
            "results_stdout_pattern": r"^(\w+),([0-9.]+)$",
        },
    )

    check_env_success(
        local_env,
        tunable_groups,
        expected_results={
            "latency": 111.0,
            "throughput": 222.0,
            "score": 0.999,
            # a, b are missing here
        },
        expected_telemetry=[],
    )


def test_local_env_file_stdout(tunable_groups: TunableGroups) -> None:
    """Print benchmark results to *BOTH* stdout and a file and extract the results from
    both.
    """
    local_env = create_local_env(
        tunable_groups,
        {
            "run": [
                "echo 'latency,111'",
                "echo 'throughput,222'",
                "echo 'score,0.999'",
                "echo 'stdout-msg,string'",
                "echo '-------------------'",  # Should be ignored
                "echo 'metric,value' > output.csv",
                "echo 'extra1,333' >> output.csv",
                "echo 'extra2,444' >> output.csv",
                "echo 'file-msg,string' >> output.csv",
            ],
            "results_stdout_pattern": r"([a-zA-Z0-9_-]+),([a-z0-9.]+)",
            "read_results_file": "output.csv",
        },
    )

    check_env_success(
        local_env,
        tunable_groups,
        expected_results={
            "latency": 111.0,
            "throughput": 222.0,
            "score": 0.999,
            "stdout-msg": "string",
            "extra1": 333.0,
            "extra2": 444.0,
            "file-msg": "string " if sys.platform == "win32" else "string",
        },
        expected_telemetry=[],
    )
