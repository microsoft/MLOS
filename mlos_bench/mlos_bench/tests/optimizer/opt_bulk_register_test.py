#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for mock mlos_bench optimizer.
"""

from typing import List

import pytest

from mlos_bench.optimizer import Optimizer, MockOptimizer, MlosCoreOptimizer

# pylint: disable=redefined-outer-name


@pytest.fixture
def mock_configs_data() -> List[dict]:
    """
    Mock benchmark results from earlier experiments.
    """
    return [
        {
            'vmSize': 'Standard_B4ms',
            'rootfs': 'xfs',
            'kernel_sched_migration_cost_ns': 40000,
            'score': 88.88
        },
        {
            'vmSize': 'Standard_B4ms',
            'rootfs': 'ext4',
            'kernel_sched_migration_cost_ns': 100000,
            'score': 66.66
        },
        {
            'vmSize': 'Standard_B2s',
            'rootfs': 'xfs',
            'kernel_sched_migration_cost_ns': 200000,
            'score': 99.99
        }
    ]


def _test_opt_update_min(opt: Optimizer, data: List[dict]):
    """
    Test the bulk update of the optimizer on the minimization problem.
    """
    opt.bulk_register(data)
    (score, tunables) = opt.get_best_observation()
    assert score == pytest.approx(66.66, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B4ms",
        "rootfs": "ext4",
        "kernel_sched_migration_cost_ns": 100000,
    }


def _test_opt_update_max(opt: Optimizer, data: List[dict]):
    """
    Test the bulk update of the optimizer on the maximiation prtoblem.
    """
    opt.bulk_register(data)
    (score, tunables) = opt.get_best_observation()
    assert score == pytest.approx(99.99, 0.01)
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B2s",
        "rootfs": "xfs",
        "kernel_sched_migration_cost_ns": 200000,
    }


def test_update_mock_min(mock_opt: MockOptimizer,
                         mock_configs_data: List[dict]):
    """
    Test the bulk update of the mock optimizer on the minimization problem.
    """
    _test_opt_update_min(mock_opt, mock_configs_data)


def test_update_mock_max(mock_opt_max: MockOptimizer,
                         mock_configs_data: List[dict]):
    """
    Test the bulk update of the mock optimizer on the maximization problem.
    """
    _test_opt_update_max(mock_opt_max, mock_configs_data)


def test_update_emukit(emukit_opt: MlosCoreOptimizer,
                       mock_configs_data: List[dict]):
    """
    Test the bulk update of the EmuKit optimizer.
    """
    _test_opt_update_min(emukit_opt, mock_configs_data)


def test_update_emukit_max(emukit_opt_max: MlosCoreOptimizer,
                           mock_configs_data: List[dict]):
    """
    Test the bulk update of the EmuKit optimizer on the maximization problem.
    """
    _test_opt_update_max(emukit_opt_max, mock_configs_data)


def test_update_scikit_gp(scikit_gp_opt: MlosCoreOptimizer,
                          mock_configs_data: List[dict]):
    """
    Test the bulk update of the scikit-optimize GP optimizer.
    """
    _test_opt_update_min(scikit_gp_opt, mock_configs_data)


def test_update_scikit_et(scikit_et_opt: MlosCoreOptimizer,
                          mock_configs_data: List[dict]):
    """
    Test the bulk update of the scikit-optimize ET optimizer.
    """
    _test_opt_update_min(scikit_et_opt, mock_configs_data)
