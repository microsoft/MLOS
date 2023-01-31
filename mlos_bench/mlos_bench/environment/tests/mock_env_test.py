"""
Unit tests for mock benchmark environment.
"""

import pytest

from mlos_bench.environment import Status, TunableGroups
from mlos_bench.environment.mock_env import MockEnv

# pylint: disable=redefined-outer-name


@pytest.fixture
def tunable_groups() -> TunableGroups:
    """
    A test fixture that produces a mock TunableGroups.

    Returns
    -------
    tunable_groups : TunableGroups
        A new TunableGroups object for testing.
    """
    tunables = TunableGroups({
        "provision": {
            "cost": 1000,
            "params": {
                "vmSize": {
                    "description": "Azure VM size",
                    "type": "categorical",
                    "default": "Standard_B4ms",
                    "values": ["Standard_B2s", "Standard_B2ms", "Standard_B4ms"]
                }
            }
        },

        "boot": {
            "cost": 300,
            "params": {
                "rootfs": {
                    "description": "Root file system",
                    "type": "categorical",
                    "default": "xfs",
                    "values": ["xfs", "ext4", "ext2"]
                }
            }
        },

        "kernel": {
            "cost": 1,
            "params": {
                "kernel_sched_migration_cost_ns": {
                    "description": "Cost of migrating the thread to another core",
                    "type": "int",
                    "default": -1,
                    "range": [-1, 500000],
                    "special": [-1]
                }
            }
        }
    })
    tunables.reset()
    return tunables


@pytest.fixture
def mock_env(tunable_groups: TunableGroups) -> MockEnv:
    """
    Test fixture for MockEnv.
    """
    return MockEnv(
        "Test Env",
        config={
            "tunable_groups": ["provision", "boot", "kernel"],
            "seed": 13,
            "range": [60, 120]
        },
        tunables=tunable_groups
    )


@pytest.fixture
def mock_env_no_noise(tunable_groups: TunableGroups) -> MockEnv:
    """
    Test fixture for MockEnv.
    """
    return MockEnv(
        "Test Env No Noise",
        config={
            "tunable_groups": ["provision", "boot", "kernel"],
            "range": [60, 120]
        },
        tunables=tunable_groups
    )


def test_mock_env_default(mock_env: MockEnv, tunable_groups: TunableGroups):
    """
    Check the default values of the mock environment.
    """
    assert mock_env.setup(tunable_groups)
    (status, data) = mock_env.benchmark()
    assert status == Status.SUCCEEDED
    assert data.loc[0, "benchmark"] == pytest.approx(78.45, 0.01)
    # Second time, results should differ because of the noise.
    (status, data) = mock_env.benchmark()
    assert status == Status.SUCCEEDED
    assert data.loc[0, "benchmark"] == pytest.approx(98.21, 0.01)


def test_mock_env_no_noise(mock_env_no_noise: MockEnv, tunable_groups: TunableGroups):
    """
    Check the default values of the mock environment.
    """
    assert mock_env_no_noise.setup(tunable_groups)
    for _ in range(10):
        # Noise-free results should be the same every time.
        (status, data) = mock_env_no_noise.benchmark()
        assert status == Status.SUCCEEDED
        assert data.loc[0, "benchmark"] == pytest.approx(80.11, 0.01)


def test_mock_env_assign(mock_env: MockEnv, tunable_groups: TunableGroups):
    """
    Check the benchmark values of the mock environment after the assignment.
    """
    tunable_groups.assign({
        "vmSize": "Standard_B2ms",
        "rootfs": "ext4",
        "kernel_sched_migration_cost_ns": 250000
    })
    assert mock_env.setup(tunable_groups)
    (status, data) = mock_env.benchmark()
    assert status == Status.SUCCEEDED
    assert data.loc[0, "benchmark"] == pytest.approx(73.4, 0.01)
