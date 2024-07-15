#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for LocalEnv benchmark environment."""
import pytest

from mlos_bench.tests.environments import check_env_success
from mlos_bench.tests.environments.local import create_local_env
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_local_env(tunable_groups: TunableGroups) -> None:
    """Produce benchmark and telemetry data in a local script and read it."""
    local_env = create_local_env(
        tunable_groups,
        {
            "run": [
                "echo 'metric,value' > output.csv",
                "echo 'latency,10' >> output.csv",
                "echo 'throughput,66' >> output.csv",
                "echo 'score,0.9' >> output.csv",
            ],
            "read_results_file": "output.csv",
        },
    )

    check_env_success(
        local_env,
        tunable_groups,
        expected_results={
            "latency": 10.0,
            "throughput": 66.0,
            "score": 0.9,
        },
        expected_telemetry=[],
    )


def test_local_env_service_context(tunable_groups: TunableGroups) -> None:
    """Basic check that context support for Service mixins are handled when environment
    contexts are entered.
    """
    local_env = create_local_env(tunable_groups, {"run": ["echo NA"]})
    # pylint: disable=protected-access
    assert local_env._service
    assert not local_env._service._in_context
    assert not local_env._service._service_contexts
    with local_env as env_context:
        assert env_context._in_context
        assert local_env._service._in_context
        assert local_env._service._service_contexts  # type: ignore[unreachable] # (false positive)
        assert all(svc._in_context for svc in local_env._service._service_contexts)
        assert all(svc._in_context for svc in local_env._service._services)
    assert not local_env._service._in_context  # type: ignore[unreachable] # (false positive)
    assert not local_env._service._service_contexts
    assert not any(svc._in_context for svc in local_env._service._services)


def test_local_env_results_no_header(tunable_groups: TunableGroups) -> None:
    """Fail if the results are not in the expected format."""
    local_env = create_local_env(
        tunable_groups,
        {
            "run": [
                # No header
                "echo 'latency,10' > output.csv",
                "echo 'throughput,66' >> output.csv",
                "echo 'score,0.9' >> output.csv",
            ],
            "read_results_file": "output.csv",
        },
    )

    with local_env as env_context:
        assert env_context.setup(tunable_groups)
        with pytest.raises(ValueError):
            env_context.run()


def test_local_env_wide(tunable_groups: TunableGroups) -> None:
    """Produce benchmark data in wide format and read it."""
    local_env = create_local_env(
        tunable_groups,
        {
            "run": [
                "echo 'latency,throughput,score' > output.csv",
                "echo '10,66,0.9' >> output.csv",
            ],
            "read_results_file": "output.csv",
        },
    )

    check_env_success(
        local_env,
        tunable_groups,
        expected_results={
            "latency": 10,
            "throughput": 66,
            "score": 0.9,
        },
        expected_telemetry=[],
    )
