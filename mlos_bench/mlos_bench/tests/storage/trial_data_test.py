#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for loading the trial metadata.
"""

import pytest

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_exp_trial_data(exp_data: ExperimentData,
                        tunable_groups: TunableGroups) -> None:
    """
    Start a new trial and check the storage for the trial data.
    """
    trial = exp_data.trials[1]
    assert trial.status == Status.SUCCEEDED
    assert trial.tunable_config_dict == tunable_groups.get_param_values()
    assert trial.metadata_dict["trial_number"] == 1
    assert list(trial.results_dict.keys()) == ["score"]
    assert trial.results_dict["score"] == pytest.approx(5.0, rel=0.1)
    # TODO: test telemetry data too


def test_exp_trial_data_config_trial_group_id(exp_data: ExperimentData) -> None:
    """
    Test the config_trial_group_id property of TrialData.
    """
    # First three trials should use the same config.
    trial_1 = exp_data.trials[1]
    assert trial_1.config_id == 1
    assert trial_1.config_trial_group_id == 1

    trial_2 = exp_data.trials[2]
    assert trial_2.config_id == 1
    assert trial_2.config_trial_group_id == 1

    # The fourth, should be a new config.
    trial_4 = exp_data.trials[4]
    assert trial_4.config_id == 2
    assert trial_4.config_trial_group_id == 4
