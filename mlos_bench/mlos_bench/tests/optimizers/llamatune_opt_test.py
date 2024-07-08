#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for mock mlos_bench optimizer."""

import pytest

from mlos_bench.environments.status import Status
from mlos_bench.optimizers.mlos_core_optimizer import MlosCoreOptimizer
from mlos_bench.tests import SEED
from mlos_bench.tunables.tunable_groups import TunableGroups

# pylint: disable=redefined-outer-name


@pytest.fixture
def llamatune_opt(tunable_groups: TunableGroups) -> MlosCoreOptimizer:
    """Test fixture for mlos_core SMAC optimizer."""
    return MlosCoreOptimizer(
        tunables=tunable_groups,
        service=None,
        config={
            "space_adapter_type": "LLAMATUNE",
            "space_adapter_config": {
                "num_low_dims": 2,
            },
            "optimization_targets": {"score": "min"},
            "max_suggestions": 10,
            "optimizer_type": "SMAC",
            "seed": SEED,
            # "start_with_defaults": False,
        },
    )


@pytest.fixture
def mock_scores() -> list:
    """A list of fake benchmark scores to test the optimizers."""
    return [88.88, 66.66, 99.99]


def test_llamatune_optimizer(llamatune_opt: MlosCoreOptimizer, mock_scores: list) -> None:
    """Make sure that llamatune+smac optimizer initializes and works correctly."""
    for score in mock_scores:
        assert llamatune_opt.not_converged()
        tunables = llamatune_opt.suggest()
        # FIXME: Emukit optimizer is not deterministic, so we can't check the tunables here.
        llamatune_opt.register(tunables, Status.SUCCEEDED, {"score": score})

    (best_score, best_tunables) = llamatune_opt.get_best_observation()
    assert best_score is not None and len(best_score) == 1
    assert isinstance(best_tunables, TunableGroups)
    assert best_score["score"] == pytest.approx(66.66, 0.01)


if __name__ == "__main__":
    # For attaching debugger debugging:
    pytest.main(["-vv", "-n1", "-k", "test_llamatune_optimizer", __file__])
