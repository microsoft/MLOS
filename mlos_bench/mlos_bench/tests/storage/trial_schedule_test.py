#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for scheduling trials for some future time.
"""
from datetime import datetime, timedelta

from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_schedule_trial(exp_storage: Storage.Experiment,
                        tunable_groups: TunableGroups) -> None:
    """
    Schedule several trials for future execution and retrieve them later at certain timestamps.
    """
    timedelta_1h = timedelta(hours=1)
    timestamp = datetime.utcnow()
    config = {"location": "westus2", "num_repeats": 10}

    # Default, schedule ASAP:
    trial_now1 = exp_storage.new_trial(tunable_groups, config=config)
    # Schedule with explicit current timestamp:
    trial_now2 = exp_storage.new_trial(tunable_groups, timestamp, config)
    # Schedule 1 hour in the future:
    trial_1h = exp_storage.new_trial(tunable_groups, timestamp + timedelta_1h, config)
    # Schedule 2 hours in the future:
    trial_2h = exp_storage.new_trial(tunable_groups, timestamp + timedelta_1h * 2, config)

    # Get trials scheduled to run now:
    pending_ids = set(t.trial_id for t in exp_storage.pending_trials(timestamp, running=False))
    assert pending_ids == {trial_now1.trial_id, trial_now2.trial_id}

    # Get trials scheduled to run within the next 1 hour:
    pending_ids = set(t.trial_id for t in exp_storage.pending_trials(timestamp + timedelta_1h, running=False))
    assert pending_ids == {trial_now1.trial_id, trial_now2.trial_id, trial_1h.trial_id}

    # Get trials scheduled to run within the next 3 hours:
    pending_ids = set(t.trial_id for t in exp_storage.pending_trials(timestamp + timedelta_1h * 3, running=False))
    assert pending_ids == {trial_now1.trial_id, trial_now2.trial_id, trial_1h.trial_id, trial_2h.trial_id}
