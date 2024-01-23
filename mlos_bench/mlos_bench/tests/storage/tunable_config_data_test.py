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
