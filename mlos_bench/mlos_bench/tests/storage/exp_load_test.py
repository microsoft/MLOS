#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for the storage subsystem.
"""
import pytest

from mlos_bench.environment.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.storage.base_storage import Storage


def test_exp_load_empty(exp_storage_memory_sql: Storage.Experiment) -> None:
    """
    Try to retrieve old experimental data from the empty storage.
    """
    (configs, scores) = exp_storage_memory_sql.load()
    assert not configs
    assert not scores


def test_exp_pending_empty(exp_storage_memory_sql: Storage.Experiment) -> None:
    """
    Try to retrieve pending experiments from the empty storage.
    """
    trials = list(exp_storage_memory_sql.pending_trials())
    assert not trials


def test_exp_trial_pending(exp_storage_memory_sql: Storage.Experiment,
                           tunable_groups: TunableGroups) -> None:
    """
    Start a trial and check that it is pending.
    """
    trial = exp_storage_memory_sql.new_trial(tunable_groups)
    (pending,) = list(exp_storage_memory_sql.pending_trials())
    assert pending.trial_id == trial.trial_id
    assert pending.tunables == tunable_groups


def test_exp_trial_pending_many(exp_storage_memory_sql: Storage.Experiment,
                                tunable_groups: TunableGroups) -> None:
    """
    Start THREE trials and check that both are pending.
    """
    config1 = tunable_groups.copy().assign({'rootfs': 'ext4'})
    config2 = tunable_groups.copy().assign({'rootfs': 'ext2'})
    trial_ids = {
        exp_storage_memory_sql.new_trial(config1).trial_id,
        exp_storage_memory_sql.new_trial(config2).trial_id,
        exp_storage_memory_sql.new_trial(config2).trial_id,  # Submit same config twice
    }
    pending_ids = {pending.trial_id for pending in exp_storage_memory_sql.pending_trials()}
    assert len(pending_ids) == 3
    assert trial_ids == pending_ids


def test_exp_trial_pending_fail(exp_storage_memory_sql: Storage.Experiment,
                                tunable_groups: TunableGroups) -> None:
    """
    Start a trial, fail it, and and check that it is NOT pending.
    """
    trial = exp_storage_memory_sql.new_trial(tunable_groups)
    trial.update(Status.FAILED)
    trials = list(exp_storage_memory_sql.pending_trials())
    assert not trials


def test_exp_trial_success(exp_storage_memory_sql: Storage.Experiment,
                           tunable_groups: TunableGroups) -> None:
    """
    Start a trial, finish it successfully, and and check that it is NOT pending.
    """
    trial = exp_storage_memory_sql.new_trial(tunable_groups)
    trial.update(Status.SUCCEEDED, 99.9)
    trials = list(exp_storage_memory_sql.pending_trials())
    assert not trials


def test_exp_trial_update_twice(exp_storage_memory_sql: Storage.Experiment,
                                tunable_groups: TunableGroups) -> None:
    """
    Update the trial status twice and receive an error.
    """
    trial = exp_storage_memory_sql.new_trial(tunable_groups)
    trial.update(Status.FAILED)
    with pytest.raises(RuntimeError):
        trial.update(Status.SUCCEEDED, 99.9)


def test_exp_trial_pending_3(exp_storage_memory_sql: Storage.Experiment,
                             tunable_groups: TunableGroups) -> None:
    """
    Start THREE trials, let one succeed, another one fail and keep one not updated.
    Check that one is still pending another one can be loaded into the optimizer.
    """
    score = 99.9

    trial_fail = exp_storage_memory_sql.new_trial(tunable_groups)
    trial_succ = exp_storage_memory_sql.new_trial(tunable_groups)
    trial_pend = exp_storage_memory_sql.new_trial(tunable_groups)

    trial_fail.update(Status.FAILED)
    trial_succ.update(Status.SUCCEEDED, score)

    (pending,) = list(exp_storage_memory_sql.pending_trials())
    assert pending.trial_id == trial_pend.trial_id

    (configs, scores) = exp_storage_memory_sql.load()
    assert len(configs) == 1
    assert len(scores) == 1
    assert scores[0] == score
    assert tunable_groups.copy().assign(configs[0]).reset() == trial_succ.tunables
