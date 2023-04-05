#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for the storage subsystem.
"""

from mlos_bench.storage import Storage
from mlos_bench.tunables import TunableGroups
from mlos_bench.environment import Status

# pylint: disable=redefined-outer-name


def test_exp_load_empty(exp_storage_memory_sql: Storage.Experiment):
    """
    Try to retrieve old experimental data from the empty storage.
    """
    (configs, scores) = exp_storage_memory_sql.load()
    assert not configs
    assert not scores


def test_exp_pending_empty(exp_storage_memory_sql: Storage.Experiment):
    """
    Try to retrieve pending experiments from the empty storage.
    """
    trials = list(exp_storage_memory_sql.pending())
    assert not trials


def test_exp_trial_pending(exp_storage_memory_sql: Storage.Experiment,
                           tunable_groups: TunableGroups):
    """
    Start a trial and check that it is pending.
    """
    trial = exp_storage_memory_sql.trial(tunable_groups)
    (pending,) = list(exp_storage_memory_sql.pending())
    assert pending.trial_id == trial.trial_id
    assert pending.tunables == tunable_groups


def test_exp_trial_pending_2(exp_storage_memory_sql: Storage.Experiment,
                             tunable_groups: TunableGroups):
    """
    Start TWO trials and check that both are pending.
    """
    config1 = tunable_groups.copy().assign({'rootfs': 'ext4'})
    config2 = tunable_groups.copy().assign({'rootfs': 'ext2'})
    trial1 = exp_storage_memory_sql.trial(config1)
    trial2 = exp_storage_memory_sql.trial(config2)
    pending = list(exp_storage_memory_sql.pending())
    assert len(pending) == 2
    assert {pending[0].trial_id, pending[1].trial_id} == {trial1.trial_id, trial2.trial_id}


def test_exp_trial_pending_fail(exp_storage_memory_sql: Storage.Experiment,
                                tunable_groups: TunableGroups):
    """
    Start a trial, fail it, and and check that it is NOT pending.
    """
    trial = exp_storage_memory_sql.trial(tunable_groups)
    trial.update(Status.FAILED)
    trials = list(exp_storage_memory_sql.pending())
    assert not trials


def test_exp_trial_success(exp_storage_memory_sql: Storage.Experiment,
                           tunable_groups: TunableGroups):
    """
    Start a trial, finish it successfully, and and check that it is NOT pending.
    """
    trial = exp_storage_memory_sql.trial(tunable_groups)
    trial.update(Status.SUCCEEDED, {'score': 99.9})
    trials = list(exp_storage_memory_sql.pending())
    assert not trials


def test_exp_trial_pending_3(exp_storage_memory_sql: Storage.Experiment,
                             tunable_groups: TunableGroups):
    """
    Start THREE trials, let one succeed, another one fail and keep one not updated.
    Check that one is still pending another one can be loaded into the optimizer.
    """
    score = 99.9

    trial_fail = exp_storage_memory_sql.trial(tunable_groups)
    trial_succ = exp_storage_memory_sql.trial(tunable_groups)
    trial_pend = exp_storage_memory_sql.trial(tunable_groups)

    trial_fail.update(Status.FAILED)
    trial_succ.update(Status.SUCCEEDED, {'score': score})

    (pending,) = list(exp_storage_memory_sql.pending())
    assert pending.trial_id == trial_pend.trial_id

    (configs, scores) = exp_storage_memory_sql.load()
    assert len(configs) == 1
    assert len(scores) == 1
    assert scores[0] == score
    assert tunable_groups.copy().assign(configs[0]).reset() == trial_succ.tunables
