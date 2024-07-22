#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for mock benchmark environment."""
import pytest

from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_mock_env_default(mock_env: MockEnv, tunable_groups: TunableGroups) -> None:
    """Check the default values of the mock environment."""
    with mock_env as env_context:
        assert env_context.setup(tunable_groups)
        (status, _ts, data) = env_context.run()
        assert status.is_succeeded()
        assert data is not None
        assert data["score"] == pytest.approx(73.97, 0.01)
        # Second time, results should differ because of the noise.
        (status, _ts, data) = env_context.run()
        assert status.is_succeeded()
        assert data is not None
        assert data["score"] == pytest.approx(72.92, 0.01)


def test_mock_env_no_noise(mock_env_no_noise: MockEnv, tunable_groups: TunableGroups) -> None:
    """Check the default values of the mock environment."""
    with mock_env_no_noise as env_context:
        assert env_context.setup(tunable_groups)
        for _ in range(10):
            # Noise-free results should be the same every time.
            (status, _ts, data) = env_context.run()
            assert status.is_succeeded()
            assert data is not None
            assert data["score"] == pytest.approx(75.0, 0.01)


@pytest.mark.parametrize(
    ("tunable_values", "expected_score"),
    [
        (
            {"vmSize": "Standard_B2ms", "idle": "halt", "kernel_sched_migration_cost_ns": 250000},
            66.4,
        ),
        (
            {"vmSize": "Standard_B4ms", "idle": "halt", "kernel_sched_migration_cost_ns": 40000},
            74.06,
        ),
    ],
)
def test_mock_env_assign(
    mock_env: MockEnv,
    tunable_groups: TunableGroups,
    tunable_values: dict,
    expected_score: float,
) -> None:
    """Check the benchmark values of the mock environment after the assignment."""
    with mock_env as env_context:
        tunable_groups.assign(tunable_values)
        assert env_context.setup(tunable_groups)
        (status, _ts, data) = env_context.run()
        assert status.is_succeeded()
        assert data is not None
        assert data["score"] == pytest.approx(expected_score, 0.01)


@pytest.mark.parametrize(
    ("tunable_values", "expected_score"),
    [
        (
            {"vmSize": "Standard_B2ms", "idle": "halt", "kernel_sched_migration_cost_ns": 250000},
            67.5,
        ),
        (
            {"vmSize": "Standard_B4ms", "idle": "halt", "kernel_sched_migration_cost_ns": 40000},
            75.1,
        ),
    ],
)
def test_mock_env_no_noise_assign(
    mock_env_no_noise: MockEnv,
    tunable_groups: TunableGroups,
    tunable_values: dict,
    expected_score: float,
) -> None:
    """Check the benchmark values of the noiseless mock environment after the
    assignment.
    """
    with mock_env_no_noise as env_context:
        tunable_groups.assign(tunable_values)
        assert env_context.setup(tunable_groups)
        for _ in range(10):
            # Noise-free environment should produce the same results every time.
            (status, _ts, data) = env_context.run()
            assert status.is_succeeded()
            assert data is not None
            assert data["score"] == pytest.approx(expected_score, 0.01)
