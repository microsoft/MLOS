"""
Unit tests for mock benchmark environment.
"""

import pytest

from mlos_bench.environment import MockEnv
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_mock_env_default(mock_env: MockEnv, tunable_groups: TunableGroups):
    """
    Check the default values of the mock environment.
    """
    assert mock_env.setup(tunable_groups)
    (status, data) = mock_env.run()
    assert status.is_succeeded
    assert data.loc[0, "score"] == pytest.approx(78.45, 0.01)
    # Second time, results should differ because of the noise.
    (status, data) = mock_env.run()
    assert status.is_succeeded
    assert data.loc[0, "score"] == pytest.approx(98.21, 0.01)


def test_mock_env_no_noise(mock_env_no_noise: MockEnv, tunable_groups: TunableGroups):
    """
    Check the default values of the mock environment.
    """
    assert mock_env_no_noise.setup(tunable_groups)
    for _ in range(10):
        # Noise-free results should be the same every time.
        (status, data) = mock_env_no_noise.run()
        assert status.is_succeeded
        assert data.loc[0, "score"] == pytest.approx(80.11, 0.01)


@pytest.mark.parametrize(('tunable_values', 'expected_score'), [
    ({
        "vmSize": "Standard_B2ms",
        "rootfs": "ext4",
        "kernel_sched_migration_cost_ns": 250000
    }, 73.97),
    ({
        "vmSize": "Standard_B4ms",
        "rootfs": "xfs",
        "kernel_sched_migration_cost_ns": 40000
    }, 79.1),
])
def test_mock_env_assign(mock_env: MockEnv, tunable_groups: TunableGroups,
                         tunable_values: dict, expected_score: float):
    """
    Check the benchmark values of the mock environment after the assignment.
    """
    tunable_groups.assign(tunable_values)
    assert mock_env.setup(tunable_groups)
    (status, data) = mock_env.run()
    assert status.is_succeeded
    assert data.loc[0, "score"] == pytest.approx(expected_score, 0.01)


@pytest.mark.parametrize(('tunable_values', 'expected_score'), [
    ({
        "vmSize": "Standard_B2ms",
        "rootfs": "ext4",
        "kernel_sched_migration_cost_ns": 250000
    }, 75.0),
    ({
        "vmSize": "Standard_B4ms",
        "rootfs": "xfs",
        "kernel_sched_migration_cost_ns": 40000
    }, 80.1),
])
def test_mock_env_no_noise_assign(mock_env_no_noise: MockEnv,
                                  tunable_groups: TunableGroups,
                                  tunable_values: dict, expected_score: float):
    """
    Check the benchmark values of the noiseless mock environment after the assignment.
    """
    tunable_groups.assign(tunable_values)
    assert mock_env_no_noise.setup(tunable_groups)
    for _ in range(10):
        # Noise-free environment should produce the same results every time.
        (status, data) = mock_env_no_noise.run()
        assert status.is_succeeded
        assert data.loc[0, "score"] == pytest.approx(expected_score, 0.01)
