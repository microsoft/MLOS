#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for loading the TunableConfigData.
"""

from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_trial_data_tunable_config_data(exp_data: ExperimentData,
                                        tunable_groups: TunableGroups) -> None:
    """
    Check expected return values for TunableConfigData.
    """
    trial_id = 1
    expected_config_id = 1
    trial = exp_data.trials[trial_id]
    tunable_config = trial.tunable_config
    assert tunable_config.tunable_config_id == expected_config_id
    # The first should be the defaults.
    assert tunable_config.config_dict == tunable_groups.get_param_values()
    assert trial.tunable_config_trial_group.tunable_config == tunable_config


def test_mixed_numerics_exp_trial_data(
        mixed_numerics_exp_data: ExperimentData,
        mixed_numerics_tunable_groups: TunableGroups) -> None:
    """
    Tests that data type conversions are retained when loading experiment data with
    mixed numeric tunable types.
    """
    trial = next(iter(mixed_numerics_exp_data.trials.values()))
    config = trial.tunable_config.config_dict
    for (tunable, _group) in mixed_numerics_tunable_groups:
        assert isinstance(config[tunable.name], tunable.dtype)
