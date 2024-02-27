#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for the storage subsystem.
"""
from datetime import datetime

import pytest

from mlos_bench.environments.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.storage.base_storage import Storage


def test_exp_load_empty(exp_storage: Storage.Experiment) -> None:
    """
    Try to retrieve old experimental data from the empty storage.
    """
    (trial_ids, configs, scores, status) = exp_storage.load()
    assert not trial_ids
    assert not configs
    assert not scores
    assert not status


def test_exp_pending_empty(exp_storage: Storage.Experiment) -> None:
    """
    Try to retrieve pending experiments from the empty storage.
    """
    trials = list(exp_storage.pending_trials(datetime.utcnow(), running=True))
    assert not trials


def test_exp_trial_pending(exp_storage: Storage.Experiment,
                           tunable_groups: TunableGroups) -> None:
    """
    Start a trial and check that it is pending.
    """
    trial = exp_storage.new_trial(tunable_groups)
    (pending,) = list(exp_storage.pending_trials(datetime.utcnow(), running=True))
    assert pending.trial_id == trial.trial_id
    assert pending.tunables == tunable_groups


def test_exp_trial_pending_many(exp_storage: Storage.Experiment,
                                tunable_groups: TunableGroups) -> None:
    """
    Start THREE trials and check that both are pending.
    """
    config1 = tunable_groups.copy().assign({'idle': 'mwait'})
    config2 = tunable_groups.copy().assign({'idle': 'noidle'})
    trial_ids = {
        exp_storage.new_trial(config1).trial_id,
        exp_storage.new_trial(config2).trial_id,
        exp_storage.new_trial(config2).trial_id,  # Submit same config twice
    }
    pending_ids = {
        pending.trial_id
        for pending in exp_storage.pending_trials(datetime.utcnow(), running=True)
    }
    assert len(pending_ids) == 3
    assert trial_ids == pending_ids


def test_exp_trial_pending_fail(exp_storage: Storage.Experiment,
                                tunable_groups: TunableGroups) -> None:
    """
    Start a trial, fail it, and and check that it is NOT pending.
    """
    trial = exp_storage.new_trial(tunable_groups)
    trial.update(Status.FAILED, datetime.utcnow())
    trials = list(exp_storage.pending_trials(datetime.utcnow(), running=True))
    assert not trials


def test_exp_trial_success(exp_storage: Storage.Experiment,
                           tunable_groups: TunableGroups) -> None:
    """
    Start a trial, finish it successfully, and and check that it is NOT pending.
    """
    trial = exp_storage.new_trial(tunable_groups)
    trial.update(Status.SUCCEEDED, datetime.utcnow(), 99.9)
    trials = list(exp_storage.pending_trials(datetime.utcnow(), running=True))
    assert not trials


def test_exp_trial_update_categ(exp_storage: Storage.Experiment,
                                tunable_groups: TunableGroups) -> None:
    """
    Update the trial with multiple metrics, some of which are categorical.
    """
    trial = exp_storage.new_trial(tunable_groups)
    trial.update(Status.SUCCEEDED, datetime.utcnow(), {"score": 99.9, "benchmark": "test"})
    assert exp_storage.load() == (
        [trial.trial_id],
        [{
            'idle': 'halt',
            'kernel_sched_latency_ns': '2000000',
            'kernel_sched_migration_cost_ns': '-1',
            'vmSize': 'Standard_B4ms'
        }],
        [99.9],
        [Status.SUCCEEDED]
    )


def test_exp_trial_update_twice(exp_storage: Storage.Experiment,
                                tunable_groups: TunableGroups) -> None:
    """
    Update the trial status twice and receive an error.
    """
    trial = exp_storage.new_trial(tunable_groups)
    trial.update(Status.FAILED, datetime.utcnow())
    with pytest.raises(RuntimeError):
        trial.update(Status.SUCCEEDED, datetime.utcnow(), 99.9)


def test_exp_trial_pending_3(exp_storage: Storage.Experiment,
                             tunable_groups: TunableGroups) -> None:
    """
    Start THREE trials, let one succeed, another one fail and keep one not updated.
    Check that one is still pending another one can be loaded into the optimizer.
    """
    score = 99.9

    trial_fail = exp_storage.new_trial(tunable_groups)
    trial_succ = exp_storage.new_trial(tunable_groups)
    trial_pend = exp_storage.new_trial(tunable_groups)

    trial_fail.update(Status.FAILED, datetime.utcnow())
    trial_succ.update(Status.SUCCEEDED, datetime.utcnow(), score)

    (pending,) = list(exp_storage.pending_trials(datetime.utcnow(), running=True))
    assert pending.trial_id == trial_pend.trial_id

    (trial_ids, configs, scores, status) = exp_storage.load()
    assert trial_ids == [trial_fail.trial_id, trial_succ.trial_id]
    assert len(configs) == 2
    assert scores == [None, score]
    assert status == [Status.FAILED, Status.SUCCEEDED]
    assert tunable_groups.copy().assign(configs[0]).reset() == trial_fail.tunables
    assert tunable_groups.copy().assign(configs[1]).reset() == trial_succ.tunables
