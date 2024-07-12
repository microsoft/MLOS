#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for mock mlos_bench optimizer."""

from typing import Dict, List, Optional

import pytest

from mlos_bench.environments.status import Status
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.optimizers.mlos_core_optimizer import MlosCoreOptimizer
from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.tunables.tunable import TunableValue

# pylint: disable=redefined-outer-name


@pytest.fixture
def mock_configs_str(mock_configs: List[dict]) -> List[dict]:
    """
    Same as `mock_config` above, but with all values converted to strings.

    (This can happen when we retrieve the data from storage).
    """
    return [{key: str(val) for (key, val) in config.items()} for config in mock_configs]


@pytest.fixture
def mock_scores() -> List[Optional[Dict[str, TunableValue]]]:
    """Mock benchmark results from earlier experiments."""
    return [
        None,
        {"score": 88.88},
        {"score": 66.66},
        {"score": 99.99},
    ]


@pytest.fixture
def mock_status() -> List[Status]:
    """Mock status values for earlier experiments."""
    return [Status.FAILED, Status.SUCCEEDED, Status.SUCCEEDED, Status.SUCCEEDED]


def _test_opt_update_min(
    opt: Optimizer,
    configs: List[dict],
    scores: List[Optional[Dict[str, TunableValue]]],
    status: Optional[List[Status]] = None,
) -> None:
    """Test the bulk update of the optimizer on the minimization problem."""
    opt.bulk_register(configs, scores, status)
    (score, tunables) = opt.get_best_observation()
    assert score is not None
    assert score["score"] == pytest.approx(66.66, 0.01)
    assert tunables is not None
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B4ms",
        "idle": "mwait",
        "kernel_sched_migration_cost_ns": -1,
        "kernel_sched_latency_ns": 3000000,
    }


def _test_opt_update_max(
    opt: Optimizer,
    configs: List[dict],
    scores: List[Optional[Dict[str, TunableValue]]],
    status: Optional[List[Status]] = None,
) -> None:
    """Test the bulk update of the optimizer on the maximization problem."""
    opt.bulk_register(configs, scores, status)
    (score, tunables) = opt.get_best_observation()
    assert score is not None
    assert score["score"] == pytest.approx(99.99, 0.01)
    assert tunables is not None
    assert tunables.get_param_values() == {
        "vmSize": "Standard_B2s",
        "idle": "mwait",
        "kernel_sched_migration_cost_ns": 200000,
        "kernel_sched_latency_ns": 4000000,
    }


def test_update_mock_min(
    mock_opt: MockOptimizer,
    mock_configs: List[dict],
    mock_scores: List[Optional[Dict[str, TunableValue]]],
    mock_status: List[Status],
) -> None:
    """Test the bulk update of the mock optimizer on the minimization problem."""
    _test_opt_update_min(mock_opt, mock_configs, mock_scores, mock_status)
    # make sure the first suggestion after bulk load is *NOT* the default config:
    assert mock_opt.suggest().get_param_values() == {
        "vmSize": "Standard_B4ms",
        "idle": "halt",
        "kernel_sched_migration_cost_ns": 13112,
        "kernel_sched_latency_ns": 796233790,
    }


def test_update_mock_min_str(
    mock_opt: MockOptimizer,
    mock_configs_str: List[dict],
    mock_scores: List[Optional[Dict[str, TunableValue]]],
    mock_status: List[Status],
) -> None:
    """Test the bulk update of the mock optimizer with all-strings data."""
    _test_opt_update_min(mock_opt, mock_configs_str, mock_scores, mock_status)


def test_update_mock_max(
    mock_opt_max: MockOptimizer,
    mock_configs: List[dict],
    mock_scores: List[Optional[Dict[str, TunableValue]]],
    mock_status: List[Status],
) -> None:
    """Test the bulk update of the mock optimizer on the maximization problem."""
    _test_opt_update_max(mock_opt_max, mock_configs, mock_scores, mock_status)


def test_update_flaml(
    flaml_opt: MlosCoreOptimizer,
    mock_configs: List[dict],
    mock_scores: List[Optional[Dict[str, TunableValue]]],
    mock_status: List[Status],
) -> None:
    """Test the bulk update of the FLAML optimizer."""
    _test_opt_update_min(flaml_opt, mock_configs, mock_scores, mock_status)


def test_update_flaml_max(
    flaml_opt_max: MlosCoreOptimizer,
    mock_configs: List[dict],
    mock_scores: List[Optional[Dict[str, TunableValue]]],
    mock_status: List[Status],
) -> None:
    """Test the bulk update of the FLAML optimizer."""
    _test_opt_update_max(flaml_opt_max, mock_configs, mock_scores, mock_status)


def test_update_smac(
    smac_opt: MlosCoreOptimizer,
    mock_configs: List[dict],
    mock_scores: List[Optional[Dict[str, TunableValue]]],
    mock_status: List[Status],
) -> None:
    """Test the bulk update of the SMAC optimizer."""
    _test_opt_update_min(smac_opt, mock_configs, mock_scores, mock_status)


def test_update_smac_max(
    smac_opt_max: MlosCoreOptimizer,
    mock_configs: List[dict],
    mock_scores: List[Optional[Dict[str, TunableValue]]],
    mock_status: List[Status],
) -> None:
    """Test the bulk update of the SMAC optimizer."""
    _test_opt_update_max(smac_opt_max, mock_configs, mock_scores, mock_status)
