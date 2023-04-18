#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for saving and retrieving additional parameters of pending trials.
"""

from mlos_bench.storage import Storage
from mlos_bench.tunables import TunableGroups


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
