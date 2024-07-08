#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Test fixtures for mlos_bench optimizers."""

from typing import List

import pytest

from mlos_bench.optimizers.mlos_core_optimizer import MlosCoreOptimizer
from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.tests import SEED
from mlos_bench.tunables.tunable_groups import TunableGroups


@pytest.fixture
def mock_configs() -> List[dict]:
    """Mock configurations of earlier experiments."""
    return [
        {
            "vmSize": "Standard_B4ms",
            "idle": "halt",
            "kernel_sched_migration_cost_ns": 50000,
            "kernel_sched_latency_ns": 1000000,
        },
        {
            "vmSize": "Standard_B4ms",
            "idle": "halt",
            "kernel_sched_migration_cost_ns": 40000,
            "kernel_sched_latency_ns": 2000000,
        },
        {
            "vmSize": "Standard_B4ms",
            "idle": "mwait",
            "kernel_sched_migration_cost_ns": -1,  # Special value
            "kernel_sched_latency_ns": 3000000,
        },
        {
            "vmSize": "Standard_B2s",
            "idle": "mwait",
            "kernel_sched_migration_cost_ns": 200000,
            "kernel_sched_latency_ns": 4000000,
        },
    ]


@pytest.fixture
def mock_opt_no_defaults(tunable_groups: TunableGroups) -> MockOptimizer:
    """Test fixture for MockOptimizer that ignores the initial configuration."""
    return MockOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "optimization_targets": {"score": "min"},
            "max_suggestions": 5,
            "start_with_defaults": False,
            "seed": SEED,
        },
    )


@pytest.fixture
def mock_opt(tunable_groups: TunableGroups) -> MockOptimizer:
    """Test fixture for MockOptimizer."""
    return MockOptimizer(
        tunables=tunable_groups,
        service=None,
        config={"optimization_targets": {"score": "min"}, "max_suggestions": 5, "seed": SEED},
    )


@pytest.fixture
def mock_opt_max(tunable_groups: TunableGroups) -> MockOptimizer:
    """Test fixture for MockOptimizer."""
    return MockOptimizer(
        tunables=tunable_groups,
        service=None,
        config={"optimization_targets": {"score": "max"}, "max_suggestions": 10, "seed": SEED},
    )


@pytest.fixture
def flaml_opt(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """Test fixture for mlos_core FLAML optimizer."""
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "optimization_targets": {"score": "min"},
            "max_suggestions": 15,
            "optimizer_type": "FLAML",
            "seed": SEED,
        },
    )


@pytest.fixture
def flaml_opt_max(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """Test fixture for mlos_core FLAML optimizer."""
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "optimization_targets": {"score": "max"},
            "max_suggestions": 15,
            "optimizer_type": "FLAML",
            "seed": SEED,
        },
    )


# FIXME: SMAC's RF model can be non-deterministic at low iterations, which are
# normally calculated as a percentage of the max_iterations and number of
# tunable dimensions, so for now we set the initial random samples equal to the
# number of iterations and control them with a seed.

SMAC_ITERATIONS = 10


@pytest.fixture
def smac_opt(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """Test fixture for mlos_core SMAC optimizer."""
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "optimization_targets": {"score": "min"},
            "max_suggestions": SMAC_ITERATIONS,
            "optimizer_type": "SMAC",
            "seed": SEED,
            "output_directory": None,
            # See Above
            "n_random_init": SMAC_ITERATIONS,
            "max_ratio": 1.0,
        },
    )


@pytest.fixture
def smac_opt_max(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """Test fixture for mlos_core SMAC optimizer."""
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "optimization_targets": {"score": "max"},
            "max_suggestions": SMAC_ITERATIONS,
            "optimizer_type": "SMAC",
            "seed": SEED,
            "output_directory": None,
            # See Above
            "n_random_init": SMAC_ITERATIONS,
            "max_ratio": 1.0,
        },
    )
