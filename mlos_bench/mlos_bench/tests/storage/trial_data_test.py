#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for loading the trial metadata.
"""

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_exp_trial_data(storage_memory_sql: Storage,
                        exp_storage_memory_sql: Storage.Experiment,
                        tunable_groups: TunableGroups) -> None:
    """
    Start a new trial and check the storage for the trial data.
    """

    exp = storage_memory_sql.experiments[exp_storage_memory_sql.experiment_id]
    trial = exp.trials[1]
    assert trial.status == Status.SUCCEEDED
    assert trial.tunable_config_dict == tunable_groups.get_param_values()
    assert trial.metadata_dict["trial_number"] == 1
    assert trial.results_dict == {"score": 1.0}
    # TODO: test telemetry data too
