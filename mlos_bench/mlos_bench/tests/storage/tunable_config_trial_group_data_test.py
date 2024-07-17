#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for loading the TunableConfigTrialGroupData."""

from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.tests.storage import CONFIG_TRIAL_REPEAT_COUNT
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_tunable_config_trial_group_data(exp_data: ExperimentData) -> None:
    """Test basic TunableConfigTrialGroupData properties."""
    trial_id = 1
    trial = exp_data.trials[trial_id]
    tunable_config_trial_group = trial.tunable_config_trial_group
    assert (
        tunable_config_trial_group.experiment_id == exp_data.experiment_id == trial.experiment_id
    )
    assert tunable_config_trial_group.tunable_config_id == trial.tunable_config_id
    assert tunable_config_trial_group.tunable_config == trial.tunable_config
    assert (
        tunable_config_trial_group
        == next(iter(tunable_config_trial_group.trials.values())).tunable_config_trial_group
    )


def test_exp_trial_data_tunable_config_trial_group_id(exp_data: ExperimentData) -> None:
    """
    Test the TunableConfigTrialGroupData property of TrialData.

    See Also:
    - test_exp_data_tunable_config_trial_group_id_in_results_df()
    - test_exp_data_tunable_config_trial_groups()

    This tests individual fetching.
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

    # And so on ...


def test_tunable_config_trial_group_results_df(
    exp_data: ExperimentData,
    tunable_groups: TunableGroups,
) -> None:
    """Tests the results_df property of the TunableConfigTrialGroup."""
    tunable_config_id = 2
    expected_group_id = 4
    tunable_config_trial_group = exp_data.tunable_config_trial_groups[tunable_config_id]
    results_df = tunable_config_trial_group.results_df
    # We shouldn't have the results for the other configs, just this one.
    expected_count = CONFIG_TRIAL_REPEAT_COUNT
    assert len(results_df) == expected_count
    assert (
        len(results_df[(results_df["tunable_config_id"] == tunable_config_id)]) == expected_count
    )
    assert len(results_df[(results_df["tunable_config_id"] != tunable_config_id)]) == 0
    assert (
        len(results_df[(results_df["tunable_config_trial_group_id"] == expected_group_id)])
        == expected_count
    )
    assert len(results_df[(results_df["tunable_config_trial_group_id"] != expected_group_id)]) == 0
    assert len(results_df["trial_id"].unique()) == expected_count
    obj_target = next(iter(exp_data.objectives))
    assert len(results_df[ExperimentData.RESULT_COLUMN_PREFIX + obj_target]) == expected_count
    (tunable, _covariant_group) = next(iter(tunable_groups))
    assert len(results_df[ExperimentData.CONFIG_COLUMN_PREFIX + tunable.name]) == expected_count


def test_tunable_config_trial_group_trials(exp_data: ExperimentData) -> None:
    """Tests the trials property of the TunableConfigTrialGroup."""
    tunable_config_id = 2
    expected_group_id = 4
    tunable_config_trial_group = exp_data.tunable_config_trial_groups[tunable_config_id]
    trials = tunable_config_trial_group.trials
    assert len(trials) == CONFIG_TRIAL_REPEAT_COUNT
    assert all(
        trial.tunable_config_trial_group.tunable_config_trial_group_id == expected_group_id
        for trial in trials.values()
    )
    assert all(
        trial.tunable_config_id == tunable_config_id
        for trial in tunable_config_trial_group.trials.values()
    )
    assert (
        exp_data.trials[expected_group_id] == tunable_config_trial_group.trials[expected_group_id]
    )
