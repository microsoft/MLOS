#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Test fixtures for mlos_bench optimizers.
"""

import pytest

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.optimizers.mlos_core_optimizer import MlosCoreOptimizer

from mlos_bench.tests import SEED


@pytest.fixture
def mock_opt_no_defaults(tunable_groups: TunableGroups) -> MockOptimizer:
    """
    Test fixture for MockOptimizer that ignores the initial configuration.
    """
    return MockOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "optimization_target": "score",
            "optimization_direction": "min",
            "max_iterations": 5,
            "start_with_defaults": False,
            "seed": SEED
        },
    )


@pytest.fixture
def mock_opt(tunable_groups: TunableGroups) -> MockOptimizer:
    """
    Test fixture for MockOptimizer.
    """
    return MockOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "optimization_target": "score",
            "optimization_direction": "min",
            "max_iterations": 5,
            "seed": SEED
        },
    )


@pytest.fixture
def mock_opt_max(tunable_groups: TunableGroups) -> MockOptimizer:
    """
    Test fixture for MockOptimizer.
    """
    return MockOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "optimization_target": "score",
            "optimization_direction": "max",
            "max_iterations": 10,
            "seed": SEED
        },
    )


@pytest.fixture
def flaml_opt(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """
    Test fixture for mlos_core FLAML optimizer.
    """
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "optimization_target": "score",
            "optimization_direction": "min",
            "max_iterations": 5,
            "optimizer_type": "FLAML",
            "seed": SEED,
        },
    )


@pytest.fixture
def flaml_opt_max(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """
    Test fixture for mlos_core FLAML optimizer.
    """
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "optimization_target": "score",
            "optimization_direction": "max",
            "max_iterations": 5,
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
    """
    Test fixture for mlos_core SMAC optimizer.
    """
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "optimization_target": "score",
            "optimization_direction": "min",
            "max_iterations": SMAC_ITERATIONS,
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
    """
    Test fixture for mlos_core SMAC optimizer.
    """
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "optimization_target": "score",
            "optimization_direction": "max",
            "max_iterations": SMAC_ITERATIONS,
            "optimizer_type": "SMAC",
            "seed": SEED,
            "output_directory": None,
            # See Above
            "n_random_init": SMAC_ITERATIONS,
            "max_ratio": 1.0,
        },
    )
