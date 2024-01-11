#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for loading the trial metadata.
"""

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.storage.base_storage import Storage


def test_exp_trial_data_objectives(storage_memory_sql: Storage,
                                   exp_storage_memory_sql: Storage.Experiment,
                                   tunable_groups: TunableGroups) -> None:
    """
    Start a new trial and check the storage for the trial data.
    """

    trial_opt_new = exp_storage_memory_sql.new_trial(tunable_groups, config={
        "opt_target": "some-other-target",
        "opt_direction": "max",
    })
    assert trial_opt_new.config() == {
        "experiment_id": exp_storage_memory_sql.experiment_id,
        "trial_id": trial_opt_new.trial_id,
        "opt_target": "some-other-target",
        "opt_direction": "max",
    }

    trial_opt_old = exp_storage_memory_sql.new_trial(tunable_groups, config={
        "opt_target": "back-compat",
        # "opt_direction": "max",   # missing
    })
    assert trial_opt_old.config() == {
        "experiment_id": exp_storage_memory_sql.experiment_id,
        "trial_id": trial_opt_old.trial_id,
        "opt_target": "back-compat",
    }

    exp = storage_memory_sql.experiments[exp_storage_memory_sql.experiment_id]
    # objectives should be the combination of both the trial objectives and the experiment objectives
    assert exp.objectives == {
        "back-compat": None,
        "some-other-target": "max",
        exp_storage_memory_sql.opt_target: exp_storage_memory_sql.opt_direction,
    }
