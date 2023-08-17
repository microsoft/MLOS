#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for LocalEnv benchmark environment.
"""
import pytest

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.tests.environments.local import create_local_env


def test_local_env(tunable_groups: TunableGroups) -> None:
    """
    Produce benchmark and telemetry data in a local script and read it.
    """
    local_env = create_local_env(tunable_groups, {
        "run": [
            "echo 'metric,value' > output.csv",
            "echo 'latency,10' >> output.csv",
            "echo 'throughput,66' >> output.csv",
            "echo 'score,0.9' >> output.csv",
        ],
        "read_results_file": "output.csv",
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
        assert not telemetry


def test_local_env_results_no_header(tunable_groups: TunableGroups) -> None:
    """
    Fail if the results are not in the expected format.
    """
    local_env = create_local_env(tunable_groups, {
        "run": [
            # No header
            "echo 'latency,10' > output.csv",
            "echo 'throughput,66' >> output.csv",
            "echo 'score,0.9' >> output.csv",
        ],
        "read_results_file": "output.csv",
    })

    with local_env as env_context:
        assert env_context.setup(tunable_groups)
        with pytest.raises(ValueError):
            env_context.run()


def test_local_env_wide(tunable_groups: TunableGroups) -> None:
    """
    Produce benchmark data in wide format and read it.
    """
    local_env = create_local_env(tunable_groups, {
        "run": [
            "echo 'latency,throughput,score' > output.csv",
            "echo '10,66,0.9' >> output.csv",
        ],
        "read_results_file": "output.csv",
    })

    with local_env as env_context:
        assert env_context.setup(tunable_groups)
        (status, data) = env_context.run()
        assert status.is_succeeded()
        assert data == pytest.approx({
            "latency": 10,
            "throughput": 66,
            "score": 0.9,
        })
