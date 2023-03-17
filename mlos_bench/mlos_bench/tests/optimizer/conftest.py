#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Test fixtures for mlos_bench optimizers.
"""

import pytest

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.optimizer.mock_optimizer import MockOptimizer
from mlos_bench.optimizer.mlos_core_optimizer import MlosCoreOptimizer


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
def scikit_gp_opt(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
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
def scikit_et_opt(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """
    Test fixture for mlos_core Scikit optimizer.
    """
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        config={
            "max_iterations": 20,
            "optimizer_type": "SKOPT",
            "base_estimator": "et",
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
