"""
Unit tests for mock mlos_bench optimizer.
"""

import pytest

from mlos_bench.environment import Status
from mlos_bench.optimizer import MockOptimizer

# pylint: disable=redefined-outer-name


@pytest.fixture
def mock_configurations() -> list:
    """
    A list of 2-tuples of (tunable_values, score) to test the optimizers.
    """
    return [
        ({
            "vmSize": "Standard_B4ms",
            "rootfs": "xfs",
            "kernel_sched_migration_cost_ns": 13111
        }, 88.88),
        ({
            "vmSize": "Standard_B4ms",
            "rootfs": "ext4",
            "kernel_sched_migration_cost_ns": 128392
        }, 66.66),
        ({
            "vmSize": "Standard_B2s",
            "rootfs": "xfs",
            "kernel_sched_migration_cost_ns": 386122
        }, 99.99),
    ]


def test_mock_optimizer(mock_opt: MockOptimizer, mock_configurations: list):
    """
    Make sure that mock optimizer produces consistent suggestions.
    """
    for (tunable_values, score) in mock_configurations:
        assert mock_opt.not_converged()
        tunables = mock_opt.suggest()
        assert tunables.get_param_values() == tunable_values
        mock_opt.register(tunables, Status.SUCCEEDED, score)

    (score, _tunables) = mock_opt.get_best_observation()
    assert score == pytest.approx(66.66, 0.01)
