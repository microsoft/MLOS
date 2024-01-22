#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for loading the TunableConfigTrialGroupData.
"""

from mlos_bench.storage.base_experiment_data import ExperimentData


def test_exp_trial_data_tunable_config_trial_group_id(exp_data: ExperimentData) -> None:
    """
    Test the TunableConfigTrialGroupData property of TrialData.
    """
    # First three trials should use the same config.
    trial_1 = exp_data.trials[1]
    assert trial_1.tunable_config_id == 1
    assert trial_1.tunable_config_trial_group.tunable_config_trial_group_id == 1

    trial_2 = exp_data.trials[2]
    assert trial_2.tunable_config_id == 1
    assert trial_2.tunable_config_trial_group.tunable_config_trial_group_id == 1

    # The fourth, should be a new config.
    trial_4 = exp_data.trials[4]
    assert trial_4.tunable_config_id == 2
    assert trial_4.tunable_config_trial_group.tunable_config_trial_group_id == 4
