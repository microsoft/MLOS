"""
Test fixtures for mlos_bench optimizers.
"""

import pytest

from mlos_bench.environment import TunableGroups
from mlos_bench.optimizer import MockOptimizer, MlosCoreOptimizer


@pytest.fixture
def mock_opt(tunable_groups: TunableGroups) -> MockOptimizer:
    """
    Test fixture for MockOptimizer.
    """
    return MockOptimizer(
        tunables=tunable_groups,
        config={
            "max_iterations": 5,
            "seed": 42
        },
    )


@pytest.fixture
def scikit_opt(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """
    Test fixture for mlos_core Scikit optimizer.
    """
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        config={
            "max_iterations": 20,
            "optimizer_type": "SKOPT",
            "base_estimator": "gp",
            "seed": 42
        },
    )


@pytest.fixture
def emukit_opt(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """
    Test fixture for mlos_core Emukit optimizer.
    """
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        config={
            "max_iterations": 20,
            "optimizer_type": "EMUKIT"
        },
    )
