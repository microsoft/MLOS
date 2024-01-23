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


def test_exp_trial_data(exp_data: ExperimentData) -> None:
    """
    Check expected return values for TrialData.
    """
    trial = exp_data.trials[1]
    assert trial.status == Status.SUCCEEDED
    assert trial.tunable_config_id == 1
    assert trial.metadata_dict["trial_number"] == 1
    assert list(trial.results_dict.keys()) == ["score"]
    assert trial.results_dict["score"] == pytest.approx(5.0, rel=0.1)
    # TODO: test telemetry data too
