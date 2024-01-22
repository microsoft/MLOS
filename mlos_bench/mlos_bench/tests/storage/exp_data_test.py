#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for loading the experiment metadata.
"""

from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_load_empty_exp_data(storage: Storage, exp_storage: Storage.Experiment) -> None:
    """
    Try to retrieve old experimental data from the empty storage.
    """
    exp = storage.experiments[exp_storage.experiment_id]
    assert exp.experiment_id == exp_storage.experiment_id
    assert exp.description == exp_storage.description
    # Only support single objective for now.
    assert exp.objectives == {exp_storage.opt_target: exp_storage.opt_direction}


def test_exp_trial_data_objectives(storage: Storage,
                                   exp_storage: Storage.Experiment,
                                   tunable_groups: TunableGroups) -> None:
    """
    Start a new trial and check the storage for the trial data.
    """

    trial_opt_new = exp_storage.new_trial(tunable_groups, config={
        "opt_target": "some-other-target",
        "opt_direction": "max",
    })
    assert trial_opt_new.config() == {
        "experiment_id": exp_storage.experiment_id,
        "trial_id": trial_opt_new.trial_id,
        "opt_target": "some-other-target",
        "opt_direction": "max",
    }

    trial_opt_old = exp_storage.new_trial(tunable_groups, config={
        "opt_target": "back-compat",
        # "opt_direction": "max",   # missing
    })
    assert trial_opt_old.config() == {
        "experiment_id": exp_storage.experiment_id,
        "trial_id": trial_opt_old.trial_id,
        "opt_target": "back-compat",
    }

    exp = storage.experiments[exp_storage.experiment_id]
    # objectives should be the combination of both the trial objectives and the experiment objectives
    assert exp.objectives == {
        "back-compat": None,
        "some-other-target": "max",
        exp_storage.opt_target: exp_storage.opt_direction,
    }

    trial_data_opt_new = exp.trials[trial_opt_new.trial_id]
    assert trial_data_opt_new.metadata_dict == {
        "opt_target": "some-other-target",
        "opt_direction": "max",
    }


def test_exp_data_tunable_config_trial_group_id(exp_data: ExperimentData) -> None:
    """Tests the tunable_config_trial_group_id property of ExperimentData.results_df"""
    results_df = exp_data.results_df

    # First three trials should use the same config.
    trial_1_df = results_df.loc[(results_df["trial_id"] == 1)]
    assert len(trial_1_df) == 1
    assert trial_1_df["tunable_config_id"].iloc[0] == 1
    assert trial_1_df["tunable_config_trial_group_id"].iloc[0] == 1

    trial_2_df = results_df.loc[(results_df["trial_id"] == 2)]
    assert len(trial_2_df) == 1
    assert trial_2_df["tunable_config_id"].iloc[0] == 1
    assert trial_2_df["tunable_config_trial_group_id"].iloc[0] == 1

    # The fourth, should be a new config.
    trial_4_df = results_df.loc[(results_df["trial_id"] == 4)]
    assert len(trial_4_df) == 1
    assert trial_4_df["tunable_config_id"].iloc[0] == 2
    assert trial_4_df["tunable_config_trial_group_id"].iloc[0] == 4


# TODO: Check tunable_config_groups
