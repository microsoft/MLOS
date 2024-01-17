#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for loading the trial metadata.
"""

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
    assert trial.results_dict == {"score": 1.0}
    # TODO: test telemetry data too
