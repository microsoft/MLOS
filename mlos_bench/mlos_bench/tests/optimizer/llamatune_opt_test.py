#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for mock mlos_bench optimizer.
"""

import pytest

from mlos_bench.environment.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.optimizer.mlos_core_optimizer import MlosCoreOptimizer

# pylint: disable=redefined-outer-name


@pytest.fixture
def llamatune_opt(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """
    Test fixture for mlos_core Emukit optimizer.
    """
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "space_adapter_type": "LLAMATUNE",
            "space_adapter_config": {
                "num_low_dims": 1,
            },
            "minimize": "score",
            "max_iterations": 20,
            "optimizer_type": "EMUKIT",
        })


@pytest.fixture
def mock_scores() -> list:
    """
    A list of fake benchmark scores to test the optimizers.
    """
    return [88.88, 66.66, 99.99]


def test_llamatune_optimizer(llamatune_opt: MlosCoreOptimizer, mock_scores: list) -> None:
    """
    Make sure that llamatune+emukit optimizer initializes and works correctly.
    """
    for score in mock_scores:
        assert llamatune_opt.not_converged()
        tunables = llamatune_opt.suggest()
        # Emukit optimizer is not deterministic, so we can't check the tunables here.
        llamatune_opt.register(tunables, Status.SUCCEEDED, score)

    (score, _tunables) = llamatune_opt.get_best_observation()
    assert score == pytest.approx(66.66, 0.01)
