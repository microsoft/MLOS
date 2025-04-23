#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for scheduling trials for some future time."""
from collections.abc import Iterator
from datetime import datetime, timedelta

from pytz import UTC

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tests.storage import (
    CONFIG_COUNT,
    CONFIG_TRIAL_REPEAT_COUNT,
    TRIAL_RUNNER_COUNT,
)
from mlos_bench.tunables.tunable_groups import TunableGroups


def _trial_ids(trials: Iterator[Storage.Trial]) -> set[int]:
    """Extract trial IDs from a list of trials."""
    return {t.trial_id for t in trials}


def test_schedule_trial(
    storage: Storage,
    exp_storage: Storage.Experiment,
    tunable_groups: TunableGroups,
) -> None:
    # pylint: disable=too-many-locals
    """Schedule several trials for future execution and retrieve them later at certain
    timestamps.
    """
    timestamp = datetime.now(UTC)
    timedelta_1min = timedelta(minutes=1)
    timedelta_1hr = timedelta(hours=1)
    config = {"location": "westus2", "num_repeats": 10}

    # Default, schedule now:
    trial_now1 = exp_storage.new_trial(tunable_groups, config=config)
    # Schedule with explicit current timestamp:
    trial_now2 = exp_storage.new_trial(tunable_groups, timestamp, config)
    # Schedule 1 hour in the future:
    trial_1h = exp_storage.new_trial(tunable_groups, timestamp + timedelta_1hr, config)
    # Schedule 2 hours in the future:
    trial_2h = exp_storage.new_trial(tunable_groups, timestamp + timedelta_1hr * 2, config)

    # Check that if we assign a TrialRunner that that value is still available on restore.
    trial_now2.set_trial_runner(1)
    assert trial_now2.trial_runner_id

    exp_data = storage.experiments[exp_storage.experiment_id]
    trial_now1_data = exp_data.trials[trial_now1.trial_id]
    assert trial_now1_data.trial_runner_id is None
    assert trial_now1_data.status == Status.PENDING
    # Check that Status matches in object vs. backend storage.
    assert trial_now1.status == trial_now1_data.status

    trial_now2_data = exp_data.trials[trial_now2.trial_id]
    assert trial_now2_data.trial_runner_id == trial_now2.trial_runner_id

    # Scheduler side: get trials ready to run at certain timestamps:

    # Pretend 1 minute has passed, get trials scheduled to run:
    pending_ids = _trial_ids(exp_storage.pending_trials(timestamp + timedelta_1min, running=False))
    assert pending_ids == {
        trial_now1.trial_id,
        trial_now2.trial_id,
    }

    # Make sure that the pending trials and trial_runner_ids match.
    pending_trial_runner_ids = {
        pending_trial.trial_id: pending_trial.trial_runner_id
        for pending_trial in exp_storage.pending_trials(timestamp + timedelta_1min, running=False)
    }
    assert pending_trial_runner_ids == {
        trial_now1.trial_id: trial_now1.trial_runner_id,
        trial_now2.trial_id: trial_now2.trial_runner_id,
    }

    # Get trials scheduled to run within the next 1 hour:
    pending_ids = _trial_ids(exp_storage.pending_trials(timestamp + timedelta_1hr, running=False))
    assert pending_ids == {
        trial_now1.trial_id,
        trial_now2.trial_id,
        trial_1h.trial_id,
    }

    # Get trials scheduled to run within the next 3 hours:
    pending_ids = _trial_ids(
        exp_storage.pending_trials(timestamp + timedelta_1hr * 3, running=False)
    )
    assert pending_ids == {
        trial_now1.trial_id,
        trial_now2.trial_id,
        trial_1h.trial_id,
        trial_2h.trial_id,
    }

    # Optimizer side: get trials completed after some known trial:

    # No completed trials yet:
    assert exp_storage.load() == ([], [], [], [])

    # Update the status of some trials:
    trial_now1.update(Status.RUNNING, timestamp + timedelta_1min)
    trial_now2.update(Status.RUNNING, timestamp + timedelta_1min)

    # Still no completed trials:
    assert exp_storage.load() == ([], [], [], [])

    # Get trials scheduled to run within the next 3 hours:
    pending_ids = _trial_ids(
        exp_storage.pending_trials(timestamp + timedelta_1hr * 3, running=False)
    )
    assert pending_ids == {
        trial_1h.trial_id,
        trial_2h.trial_id,
    }

    # Get trials scheduled to run OR running within the next 3 hours:
    pending_ids = _trial_ids(
        exp_storage.pending_trials(timestamp + timedelta_1hr * 3, running=True)
    )
    assert pending_ids == {
        trial_now1.trial_id,
        trial_now2.trial_id,
        trial_1h.trial_id,
        trial_2h.trial_id,
    }

    # Mark some trials completed after 2 minutes:
    trial_now1.update(Status.SUCCEEDED, timestamp + timedelta_1min * 2, metrics={"score": 1.0})
    trial_now2.update(Status.FAILED, timestamp + timedelta_1min * 2)

    # Another one completes after 2 hours:
    trial_1h.update(Status.SUCCEEDED, timestamp + timedelta_1hr * 2, metrics={"score": 1.0})

    # Check that three trials have completed so far:
    (trial_ids, trial_configs, trial_scores, trial_status) = exp_storage.load()
    assert trial_ids == [trial_now1.trial_id, trial_now2.trial_id, trial_1h.trial_id]
    assert len(trial_configs) == len(trial_scores) == 3
    assert trial_status == [Status.SUCCEEDED, Status.FAILED, Status.SUCCEEDED]

    # Get only trials completed after trial_now2:
    (trial_ids, trial_configs, trial_scores, trial_status) = exp_storage.load(
        last_trial_id=trial_now2.trial_id
    )
    assert trial_ids == [trial_1h.trial_id]
    assert len(trial_configs) == len(trial_scores) == 1
    assert trial_status == [Status.SUCCEEDED]


def test_rr_scheduling(exp_data: ExperimentData) -> None:
    """Checks that the scheduler produced basic round-robin scheduling of Trials across
    TrialRunners.
    """
    for trial_id in range(1, CONFIG_COUNT * CONFIG_TRIAL_REPEAT_COUNT + 1):
        # User visible IDs start from 1.
        expected_config_id = (trial_id - 1) // CONFIG_TRIAL_REPEAT_COUNT + 1
        expected_repeat_num = (trial_id - 1) % CONFIG_TRIAL_REPEAT_COUNT + 1
        expected_runner_id = (trial_id - 1) % TRIAL_RUNNER_COUNT + 1
        trial = exp_data.trials[trial_id]
        assert trial.trial_id == trial_id, f"Expected trial_id {trial_id} for {trial}"
        assert (
            trial.tunable_config_id == expected_config_id
        ), f"Expected tunable_config_id {expected_config_id} for {trial}"
        assert (
            trial.metadata_dict["repeat_i"] == expected_repeat_num
        ), f"Expected repeat_i {expected_repeat_num} for {trial}"
        assert (
            trial.trial_runner_id == expected_runner_id
        ), f"Expected trial_runner_id {expected_runner_id} for {trial}"
