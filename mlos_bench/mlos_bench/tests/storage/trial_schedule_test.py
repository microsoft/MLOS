#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for scheduling trials for some future time."""
from datetime import datetime, timedelta
from typing import Iterator, Set

from pytz import UTC

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable_groups import TunableGroups


def _trial_ids(trials: Iterator[Storage.Trial]) -> Set[int]:
    """Extract trial IDs from a list of trials."""
    return set(t.trial_id for t in trials)


def test_schedule_trial(exp_storage: Storage.Experiment, tunable_groups: TunableGroups) -> None:
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

    # Scheduler side: get trials ready to run at certain timestamps:

    # Pretend 1 minute has passed, get trials scheduled to run:
    pending_ids = _trial_ids(exp_storage.pending_trials(timestamp + timedelta_1min, running=False))
    assert pending_ids == {
        trial_now1.trial_id,
        trial_now2.trial_id,
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
