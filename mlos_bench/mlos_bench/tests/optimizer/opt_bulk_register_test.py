#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for mock mlos_bench optimizer.
"""

from typing import Optional, List

import pytest

from mlos_bench.environment import Status
from mlos_bench.optimizer import Optimizer, MockOptimizer, MlosCoreOptimizer

# pylint: disable=redefined-outer-name


@pytest.fixture
def mock_configs() -> List[dict]:
    """
    Mock configurations of earlier experiments.
    """
    return [
        {
            'vmSize': 'Standard_B4ms',
            'rootfs': 'xfs',
            'kernel_sched_migration_cost_ns': 50000,
        },
        {
            'vmSize': 'Standard_B4ms',
            'rootfs': 'xfs',
            'kernel_sched_migration_cost_ns': 40000,
        },
        {
            'vmSize': 'Standard_B4ms',
            'rootfs': 'ext4',
            'kernel_sched_migration_cost_ns': 100000,
        },
        {
            'vmSize': 'Standard_B2s',
            'rootfs': 'xfs',
            'kernel_sched_migration_cost_ns': 200000,
        }
    ]


@pytest.fixture
def mock_scores() -> List[float]:
    """
    Mock benchmark results from earlier experiments.
    """
    return [None, 88.88, 66.66, 99.99]


@pytest.fixture
def mock_status() -> List[Status]:
    """
    Mock status values for earlier experiments.
    """
    return [Status.FAILED, Status.SUCCEEDED, Status.SUCCEEDED, Status.SUCCEEDED]


def _test_opt_update_min(opt: Optimizer, configs: List[dict],
                         scores: List[float], status: Optional[List[Status]] = None):
    """
    Test the bulk update of the optimizer on the minimization problem.
    """
    opt.bulk_register(configs, scores, status)
    (score, tunables) = opt.get_best_observation()
    assert score == pytest.approx(66.66, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B4ms",
        "rootfs": "ext4",
        "kernel_sched_migration_cost_ns": 100000,
    }


def _test_opt_update_max(opt: Optimizer, configs: List[dict],
                         scores: List[float], status: Optional[List[Status]] = None):
    """
    Test the bulk update of the optimizer on the maximiation prtoblem.
    """
    opt.bulk_register(configs, scores, status)
    (score, tunables) = opt.get_best_observation()
    assert score == pytest.approx(99.99, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B2s",
        "rootfs": "xfs",
        "kernel_sched_migration_cost_ns": 200000,
    }


def test_update_mock_min(mock_opt: MockOptimizer, mock_configs: List[dict],
                         mock_scores: List[float], mock_status: List[Status]):
    """
    Test the bulk update of the mock optimizer on the minimization problem.
    """
    _test_opt_update_min(mock_opt, mock_configs, mock_scores, mock_status)


def test_update_mock_max(mock_opt_max: MockOptimizer, mock_configs: List[dict],
                         mock_scores: List[float], mock_status: List[Status]):
    """
    Test the bulk update of the mock optimizer on the maximization problem.
    """
    _test_opt_update_max(mock_opt_max, mock_configs, mock_scores, mock_status)


def test_update_emukit(emukit_opt: MlosCoreOptimizer, mock_configs: List[dict],
                       mock_scores: List[float], mock_status: List[Status]):
    """
    Test the bulk update of the EmuKit optimizer.
    """
    _test_opt_update_min(emukit_opt, mock_configs, mock_scores, mock_status)


def test_update_emukit_max(emukit_opt_max: MlosCoreOptimizer, mock_configs: List[dict],
                           mock_scores: List[float], mock_status: List[Status]):
    """
    Test the bulk update of the EmuKit optimizer on the maximization problem.
    """
    _test_opt_update_max(emukit_opt_max, mock_configs, mock_scores, mock_status)


def test_update_scikit_gp(scikit_gp_opt: MlosCoreOptimizer, mock_configs: List[dict],
                          mock_scores: List[float], mock_status: List[Status]):
    """
    Test the bulk update of the scikit-optimize GP optimizer.
    """
    _test_opt_update_min(scikit_gp_opt, mock_configs, mock_scores, mock_status)


def test_update_scikit_et(scikit_et_opt: MlosCoreOptimizer, mock_configs: List[dict],
                          mock_scores: List[float], mock_status: List[Status]):
    """
    Test the bulk update of the scikit-optimize ET optimizer.
    """
    _test_opt_update_min(scikit_et_opt, mock_configs, mock_scores, mock_status)
