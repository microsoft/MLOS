"""
Unit tests for mock mlos_bench optimizer.
"""

import pytest

import pandas

from mlos_bench.optimizer import Optimizer, MockOptimizer, MlosCoreOptimizer

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


def _test_opt_update_min(opt: Optimizer, data: pandas.DataFrame):
    """
    Test the bulk update of the optimizer on the minimization problem.
    """
    opt.update(data)
    (score, tunables) = opt.get_best_observation()
    assert score == pytest.approx(66.66, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B4ms",
        "rootfs": "ext4",
        "kernel_sched_migration_cost_ns": 100000,
    }


def _test_opt_update_max(opt: Optimizer, data: pandas.DataFrame):
    """
    Test the bulk update of the optimizer on the maximiation prtoblem.
    """
    opt.update(data)
    (score, tunables) = opt.get_best_observation()
    assert score == pytest.approx(99.99, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B2s",
        "rootfs": "xfs",
        "kernel_sched_migration_cost_ns": 200000,
    }


def test_mock_opt_update_min(mock_opt: MockOptimizer,
                             mock_configs_df: pandas.DataFrame):
    """
    Test the bulk update of the mock optimizer on the minimization problem.
    """
    _test_opt_update_min(mock_opt, mock_configs_df)


def test_mock_opt_update_max(mock_opt_max: MockOptimizer,
                             mock_configs_df: pandas.DataFrame):
    """
    Test the bulk update of the mock optimizer on the maximization problem.
    """
    _test_opt_update_max(mock_opt_max, mock_configs_df)


def test_emukit_opt_update(emukit_opt: MlosCoreOptimizer,
                           mock_configs_df: pandas.DataFrame):
    """
    Test the bulk update of the EmuKit optimizer.
    """
    _test_opt_update_min(emukit_opt, mock_configs_df)


def test_emukit_opt_update_max(emukit_opt_max: MlosCoreOptimizer,
                               mock_configs_df: pandas.DataFrame):
    """
    Test the bulk update of the EmuKit optimizer on the maximization problem.
    """
    _test_opt_update_max(emukit_opt_max, mock_configs_df)


def test_scikit_opt_update(scikit_gp_opt: MlosCoreOptimizer,
                           mock_configs_df: pandas.DataFrame):
    """
    Test the bulk update of the scikit-optimize optimizer.
    """
    _test_opt_update_min(scikit_gp_opt, mock_configs_df)
