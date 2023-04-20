#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for saving and retrieving additional parameters of pending trials.
"""

from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_exp_trial_pending(exp_storage_memory_sql: Storage.Experiment,
                           tunable_groups: TunableGroups) -> None:
    """
    Schedule a trial and check that it is pending and has the right configuration.
    """
    config = {"location": "westus2", "num_repeats": 100}
    trial = exp_storage_memory_sql.new_trial(tunable_groups, config)
    (pending,) = list(exp_storage_memory_sql.pending_trials())
    assert pending.trial_id == trial.trial_id
    assert pending.tunables == tunable_groups
    assert pending.config() == {
        "location": "westus2",
        "num_repeats": "100",
        "experimentId": "Test-001",
        "trialId": 1,
    }


def test_exp_trial_configs(exp_storage_memory_sql: Storage.Experiment,
                           tunable_groups: TunableGroups) -> None:
    """
    Start multiple trials with two different configs and check that
    we store only two config objects in the DB.
    """
    config1 = tunable_groups.copy().assign({'rootfs': 'ext4'})
    trials1 = [
        exp_storage_memory_sql.new_trial(config1),
        exp_storage_memory_sql.new_trial(config1),
        exp_storage_memory_sql.new_trial(config1.copy()),  # Same values, different instance
    ]
    assert trials1[0].config_id == trials1[1].config_id
    assert trials1[0].config_id == trials1[2].config_id

    config2 = tunable_groups.copy().assign({'rootfs': 'xfs'})
    trials2 = [
        exp_storage_memory_sql.new_trial(config2),
        exp_storage_memory_sql.new_trial(config2),
        exp_storage_memory_sql.new_trial(config2.copy()),  # Same values, different instance
    ]
    assert trials2[0].config_id == trials2[1].config_id
    assert trials2[0].config_id == trials2[2].config_id

    assert trials1[0].config_id != trials2[0].config_id

    pending_ids = [
        pending.config_id for pending in exp_storage_memory_sql.pending_trials()
    ]
    assert len(pending_ids) == 6
    assert len(set(pending_ids)) == 2
    assert set(pending_ids) == {trials1[0].config_id, trials2[0].config_id}
