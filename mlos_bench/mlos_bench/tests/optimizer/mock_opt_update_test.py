"""
Unit tests for mock mlos_bench optimizer.
"""

import pytest

import pandas

from mlos_bench.optimizer import MockOptimizer

# pylint: disable=redefined-outer-name


@pytest.fixture
def mock_configs_df() -> pandas.DataFrame:
    """
    Mock data frame with benchmark results from earlier experiments.
    """
    return pandas.DataFrame({
        "vmSize": ["Standard_B4ms", "Standard_B4ms", "Standard_B2s"],
        "rootfs": ["xfs", "ext4", "xfs"],
        "kernel_sched_migration_cost_ns": [40000, 100000, 200000],
        "score": [88.88, 66.66, 99.99],
    })


def test_mock_opt_update(mock_opt: MockOptimizer, mock_configs_df: pandas.DataFrame):
    """
    Test the bulk update of the mock optimizer.
    """
    mock_opt.update(mock_configs_df)
    (score, tunables) = mock_opt.get_best_observation()
    assert score == pytest.approx(66.66, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B4ms",
        "rootfs": "ext4",
        "kernel_sched_migration_cost_ns": 100000,
    }
