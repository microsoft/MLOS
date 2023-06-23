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


@pytest.fixture
def mock_opt(tunable_groups: TunableGroups) -> MockOptimizer:
    """
    Test fixture for MockOptimizer.
    """
    return MockOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "minimize": "score",
            "max_iterations": 5,
            "use_defaults": True,
            "seed": 42
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
            "maximize": "score",
            "max_iterations": 10,
            "use_defaults": True,
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
        service=None,
        config={
            "minimize": "score",
            "max_iterations": 5,
            "use_defaults": True,
            "optimizer_type": "EMUKIT"
        },
    )


@pytest.fixture
def emukit_opt_max(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """
    Test fixture for mlos_core Emukit optimizer.
    """
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "maximize": "score",
            "max_iterations": 5,
            "use_defaults": True,
            "optimizer_type": "EMUKIT"
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
            "minimize": "score",
            "max_iterations": 5,
            "use_defaults": True,
            "optimizer_type": "FLAML"
        },
    )


@pytest.fixture
def smac_opt(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """
    Test fixture for mlos_core SMAC optimizer.
    """
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "minimize": "score",
            "max_iterations": 5,
            "use_defaults": True,
            "optimizer_type": "SMAC",
            "seed": 42,
        },
    )
