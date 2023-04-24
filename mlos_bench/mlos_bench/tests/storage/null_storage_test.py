#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for the no-op storage subsystem.
"""
import pytest

from mlos_bench.environment.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.null_storage import NullStorage

# pylint: disable=redefined-outer-name


@pytest.fixture
def null_experiment(tunable_groups: TunableGroups) -> Storage.Experiment:
    """
    Test fixture for mock no-op storage.
    """
    storage = NullStorage(
        tunables=tunable_groups,
        service=None,
        config={},
    )
    # pylint: disable=unnecessary-dunder-call
    return storage.experiment(
        experiment_id="Test-001",
        trial_id=1,
        root_env_config="environment.jsonc",
        description="pytest experiment",
        opt_target="score",
    ).__enter__()


def test_exp_trial_pending(null_experiment: Storage.Experiment,
                           tunable_groups: TunableGroups) -> None:
    """
    Start two new trials and check that it is *NOT* stored aywhere.
    """
    null_experiment.new_trial(tunable_groups)
    null_experiment.new_trial(tunable_groups)
    pending = list(null_experiment.pending_trials())
    assert not pending


def test_exp_trial_success(null_experiment: Storage.Experiment,
                           tunable_groups: TunableGroups) -> None:
    """
    Start a trial, finish it successfully, and and check that it is NOT pending.
    """
    trial = null_experiment.new_trial(tunable_groups)
    trial.update(Status.SUCCEEDED, 99.9)
    pending = list(null_experiment.pending_trials())
    assert not pending


def test_exp_trial_pending_3(null_experiment: Storage.Experiment,
                             tunable_groups: TunableGroups) -> None:
    """
    Start THREE trials, let one succeed, another one fail and keep one not updated.
    Check that no information is stored anywhere.
    """
    score = 99.9

    trial_fail = null_experiment.new_trial(tunable_groups)
    trial_succ = null_experiment.new_trial(tunable_groups)
    null_experiment.new_trial(tunable_groups)  # Pending trial

    trial_fail.update(Status.FAILED)
    trial_succ.update(Status.SUCCEEDED, score)

    pending = list(null_experiment.pending_trials())
    assert not pending

    (configs, scores) = null_experiment.load()
    assert len(configs) == 0
    assert len(scores) == 0
