#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for loading the TunableConfigData.
"""

from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_tunable_config_data(exp_data: ExperimentData,
                             tunable_groups: TunableGroups) -> None:
    """
    Check expected return values for TunableConfigData.
    """
    trial = exp_data.trials[1]
    tunable_config = trial.tunable_config
    assert tunable_config.tunable_config_id == 1
    assert tunable_config.config_dict == tunable_groups.get_param_values()
