#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for loading the experiment metadata."""

from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tests.storage import CONFIG_COUNT, CONFIG_TRIAL_REPEAT_COUNT
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_load_empty_exp_data(storage: Storage, exp_storage: Storage.Experiment) -> None:
    """Try to retrieve old experimental data from the empty storage."""
    exp = storage.experiments[exp_storage.experiment_id]
    assert exp.experiment_id == exp_storage.experiment_id
    assert exp.description == exp_storage.description
    assert exp.objectives == exp_storage.opt_targets


def test_exp_data_root_env_config(
    exp_storage: Storage.Experiment,
    exp_data: ExperimentData,
) -> None:
    """Tests the root_env_config property of ExperimentData."""
    # pylint: disable=protected-access
    assert exp_data.root_env_config == (
        exp_storage._root_env_config,
        exp_storage._git_repo,
        exp_storage._git_commit,
    )


def test_exp_trial_data_objectives(
    storage: Storage,
    exp_storage: Storage.Experiment,
    tunable_groups: TunableGroups,
) -> None:
    """Start a new trial and check the storage for the trial data."""

    trial_opt_new = exp_storage.new_trial(
        tunable_groups,
        config={
            "opt_target": "some-other-target",
            "opt_direction": "max",
        },
    )
    assert trial_opt_new.config() == {
        "experiment_id": exp_storage.experiment_id,
        "trial_id": trial_opt_new.trial_id,
        "opt_target": "some-other-target",
        "opt_direction": "max",
    }

    trial_opt_old = exp_storage.new_trial(
        tunable_groups,
        config={
            "opt_target": "back-compat",
            # "opt_direction": "max",   # missing
        },
    )
    assert trial_opt_old.config() == {
        "experiment_id": exp_storage.experiment_id,
        "trial_id": trial_opt_old.trial_id,
        "opt_target": "back-compat",
    }

    exp = storage.experiments[exp_storage.experiment_id]
    assert exp.objectives == exp_storage.opt_targets

    trial_data_opt_new = exp.trials[trial_opt_new.trial_id]
    assert trial_data_opt_new.metadata_dict == {
        "opt_target": "some-other-target",
        "opt_direction": "max",
    }


def test_exp_data_results_df(exp_data: ExperimentData, tunable_groups: TunableGroups) -> None:
    """Tests the results_df property of ExperimentData."""
    results_df = exp_data.results_df
    expected_trials_count = CONFIG_COUNT * CONFIG_TRIAL_REPEAT_COUNT
    assert len(results_df) == expected_trials_count
    assert len(results_df["tunable_config_id"].unique()) == CONFIG_COUNT
    assert len(results_df["trial_id"].unique()) == expected_trials_count
    obj_target = next(iter(exp_data.objectives))
    assert (
        len(results_df[ExperimentData.RESULT_COLUMN_PREFIX + obj_target]) == expected_trials_count
    )
    (tunable, _covariant_group) = next(iter(tunable_groups))
    assert (
        len(results_df[ExperimentData.CONFIG_COLUMN_PREFIX + tunable.name])
        == expected_trials_count
    )


def test_exp_data_tunable_config_trial_group_id_in_results_df(exp_data: ExperimentData) -> None:
    """
    Tests the tunable_config_trial_group_id property of ExperimentData.results_df.

    See Also: test_exp_trial_data_tunable_config_trial_group_id()
    """
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

    # And so on ...


def test_exp_data_tunable_config_trial_groups(exp_data: ExperimentData) -> None:
    """
    Tests the tunable_config_trial_groups property of ExperimentData.

    This tests bulk loading of the tunable_config_trial_groups.
    """
    # Should be keyed by config_id.
    assert list(exp_data.tunable_config_trial_groups.keys()) == list(range(1, CONFIG_COUNT + 1))
    # Which should match the objects.
    assert [
        config_trial_group.tunable_config_id
        for config_trial_group in exp_data.tunable_config_trial_groups.values()
    ] == list(range(1, CONFIG_COUNT + 1))
    # And the tunable_config_trial_group_id should also match the minimum trial_id.
    assert [
        config_trial_group.tunable_config_trial_group_id
        for config_trial_group in exp_data.tunable_config_trial_groups.values()
    ] == list(range(1, CONFIG_COUNT * CONFIG_TRIAL_REPEAT_COUNT, CONFIG_TRIAL_REPEAT_COUNT))


def test_exp_data_tunable_configs(exp_data: ExperimentData) -> None:
    """Tests the tunable_configs property of ExperimentData."""
    # Should be keyed by config_id.
    assert list(exp_data.tunable_configs.keys()) == list(range(1, CONFIG_COUNT + 1))
    # Which should match the objects.
    assert [config.tunable_config_id for config in exp_data.tunable_configs.values()] == list(
        range(1, CONFIG_COUNT + 1)
    )


def test_exp_data_default_config_id(exp_data: ExperimentData) -> None:
    """Tests the default_tunable_config_id property of ExperimentData."""
    assert exp_data.default_tunable_config_id == 1
