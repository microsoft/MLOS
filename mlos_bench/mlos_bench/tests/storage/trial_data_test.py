#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for loading the trial metadata."""

from datetime import datetime

import pytest

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_experiment_data import ExperimentData

from mlos_bench.tests.storage import CONFIG_TRIAL_REPEAT_COUNT, TRIAL_RUNNER_COUNT, CONFIG_COUNT


def test_exp_trial_data(exp_data: ExperimentData) -> None:
    """Check expected return values for TrialData."""
    trial_id = 1
    expected_config_id = 1
    expected_runner_id = 1
    expected_repeat_num = 1
    trial = exp_data.trials[trial_id]
    assert trial.trial_id == trial_id
    assert trial.tunable_config_id == expected_config_id
    assert trial.status == Status.SUCCEEDED
    assert trial.metadata_dict["repeat_i"] == expected_repeat_num
    assert trial.trial_runner_id == expected_runner_id
    assert list(trial.results_dict.keys()) == ["score"]
    assert trial.results_dict["score"] == pytest.approx(73.27, 0.01)
    assert isinstance(trial.ts_start, datetime)
    assert isinstance(trial.ts_end, datetime)
    # Note: tests for telemetry are in test_update_telemetry()


def test_rr_scheduling(exp_data: ExperimentData) -> None:
    """Checks that the scheduler produced basic round-robin scheduling of Trials across Runners."""
    for trial_id in range(1, CONFIG_COUNT * CONFIG_TRIAL_REPEAT_COUNT):
        expected_config_id = trial_id // CONFIG_TRIAL_REPEAT_COUNT + 1
        expected_repeat_num = (trial_id - 1) % CONFIG_TRIAL_REPEAT_COUNT + 1
        expected_runner_id = (trial_id - 1) % TRIAL_RUNNER_COUNT + 1
        trial = exp_data.trials[trial_id]
        assert trial.trial_id == trial_id
        assert trial.tunable_config_id == expected_config_id
        assert trial.metadata_dict["repeat_i"] == expected_repeat_num
        assert trial.trial_runner_id == expected_runner_id
