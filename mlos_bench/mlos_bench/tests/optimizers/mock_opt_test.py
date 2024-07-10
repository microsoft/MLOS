#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for mock mlos_bench optimizer."""

import pytest

from mlos_bench.environments.status import Status
from mlos_bench.optimizers.mock_optimizer import MockOptimizer

# pylint: disable=redefined-outer-name


@pytest.fixture
def mock_configurations_no_defaults() -> list:
    """A list of 2-tuples of (tunable_values, score) to test the optimizers."""
    return [
        (
            {
                "vmSize": "Standard_B4ms",
                "idle": "halt",
                "kernel_sched_migration_cost_ns": 13112,
                "kernel_sched_latency_ns": 796233790,
            },
            88.88,
        ),
        (
            {
                "vmSize": "Standard_B2ms",
                "idle": "halt",
                "kernel_sched_migration_cost_ns": 117026,
                "kernel_sched_latency_ns": 149827706,
            },
            66.66,
        ),
        (
            {
                "vmSize": "Standard_B4ms",
                "idle": "halt",
                "kernel_sched_migration_cost_ns": 354785,
                "kernel_sched_latency_ns": 795285932,
            },
            99.99,
        ),
    ]


@pytest.fixture
def mock_configurations(mock_configurations_no_defaults: list) -> list:
    """A list of 2-tuples of (tunable_values, score) to test the optimizers."""
    return [
        (
            {
                "vmSize": "Standard_B4ms",
                "idle": "halt",
                "kernel_sched_migration_cost_ns": -1,
                "kernel_sched_latency_ns": 2000000,
            },
            88.88,
        ),
    ] + mock_configurations_no_defaults


def _optimize(mock_opt: MockOptimizer, mock_configurations: list) -> float:
    """Run several iterations of the optimizer and return the best score."""
    for tunable_values, score in mock_configurations:
        assert mock_opt.not_converged()
        tunables = mock_opt.suggest()
        assert tunables.get_param_values() == tunable_values
        mock_opt.register(tunables, Status.SUCCEEDED, {"score": score})

    (scores, _tunables) = mock_opt.get_best_observation()
    assert scores is not None
    assert len(scores) == 1
    return scores["score"]


def test_mock_optimizer(mock_opt: MockOptimizer, mock_configurations: list) -> None:
    """Make sure that mock optimizer produces consistent suggestions."""
    score = _optimize(mock_opt, mock_configurations)
    assert score == pytest.approx(66.66, 0.01)


def test_mock_optimizer_no_defaults(
    mock_opt_no_defaults: MockOptimizer,
    mock_configurations_no_defaults: list,
) -> None:
    """Make sure that mock optimizer produces consistent suggestions."""
    score = _optimize(mock_opt_no_defaults, mock_configurations_no_defaults)
    assert score == pytest.approx(66.66, 0.01)


def test_mock_optimizer_max(mock_opt_max: MockOptimizer, mock_configurations: list) -> None:
    """Check the maximization mode of the mock optimizer."""
    score = _optimize(mock_opt_max, mock_configurations)
    assert score == pytest.approx(99.99, 0.01)


def test_mock_optimizer_register_fail(mock_opt: MockOptimizer) -> None:
    """Check the input acceptance conditions for Optimizer.register()."""
    tunables = mock_opt.suggest()
    mock_opt.register(tunables, Status.SUCCEEDED, {"score": 10})
    mock_opt.register(tunables, Status.FAILED)
    with pytest.raises(ValueError):
        mock_opt.register(tunables, Status.SUCCEEDED, None)
    with pytest.raises(ValueError):
        mock_opt.register(tunables, Status.FAILED, {"score": 10})
