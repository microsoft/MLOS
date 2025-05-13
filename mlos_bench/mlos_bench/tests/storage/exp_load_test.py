#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for the storage subsystem."""
from atexit import register
from datetime import datetime, timedelta, tzinfo
from random import random

from more_itertools import last
import pytest
from pytz import UTC

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tests import ZONE_INFO
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_exp_load_empty(exp_storage: Storage.Experiment) -> None:
    """Try to retrieve old experimental data from the empty storage."""
    (trial_ids, configs, scores, status) = exp_storage.load()
    assert not trial_ids
    assert not configs
    assert not scores
    assert not status


def test_exp_pending_empty(exp_storage: Storage.Experiment) -> None:
    """Try to retrieve pending experiments from the empty storage."""
    trials = list(exp_storage.pending_trials(datetime.now(UTC), running=True))
    assert not trials


@pytest.mark.parametrize(("zone_info"), ZONE_INFO)
def test_exp_trial_pending(
    exp_storage: Storage.Experiment,
    tunable_groups: TunableGroups,
    zone_info: tzinfo | None,
) -> None:
    """Start a trial and check that it is pending."""
    trial = exp_storage.new_trial(tunable_groups)
    (pending,) = list(exp_storage.pending_trials(datetime.now(zone_info), running=True))
    assert pending.trial_id == trial.trial_id
    assert pending.tunables == tunable_groups


@pytest.mark.parametrize(("zone_info"), ZONE_INFO)
def test_exp_trial_pending_many(
    exp_storage: Storage.Experiment,
    tunable_groups: TunableGroups,
    zone_info: tzinfo | None,
) -> None:
    """Start THREE trials and check that both are pending."""
    config1 = tunable_groups.copy().assign({"idle": "mwait"})
    config2 = tunable_groups.copy().assign({"idle": "noidle"})
    trial_ids = {
        exp_storage.new_trial(config1).trial_id,
        exp_storage.new_trial(config2).trial_id,
        exp_storage.new_trial(config2).trial_id,  # Submit same config twice
    }
    pending_ids = {
        pending.trial_id
        for pending in exp_storage.pending_trials(datetime.now(zone_info), running=True)
    }
    assert len(pending_ids) == 3
    assert trial_ids == pending_ids


@pytest.mark.parametrize(("zone_info"), ZONE_INFO)
def test_exp_trial_pending_fail(
    exp_storage: Storage.Experiment,
    tunable_groups: TunableGroups,
    zone_info: tzinfo | None,
) -> None:
    """Start a trial, fail it, and and check that it is NOT pending."""
    trial = exp_storage.new_trial(tunable_groups)
    trial.update(Status.FAILED, datetime.now(zone_info))
    trials = list(exp_storage.pending_trials(datetime.now(zone_info), running=True))
    assert not trials


@pytest.mark.parametrize(("zone_info"), ZONE_INFO)
def test_exp_trial_success(
    exp_storage: Storage.Experiment,
    tunable_groups: TunableGroups,
    zone_info: tzinfo | None,
) -> None:
    """Start a trial, finish it successfully, and and check that it is NOT pending."""
    trial = exp_storage.new_trial(tunable_groups)
    trial.update(Status.SUCCEEDED, datetime.now(zone_info), {"score": 99.9})
    trials = list(exp_storage.pending_trials(datetime.now(zone_info), running=True))
    assert not trials


@pytest.mark.parametrize(("zone_info"), ZONE_INFO)
def test_exp_trial_update_categ(
    exp_storage: Storage.Experiment,
    tunable_groups: TunableGroups,
    zone_info: tzinfo | None,
) -> None:
    """Update the trial with multiple metrics, some of which are categorical."""
    trial = exp_storage.new_trial(tunable_groups)
    trial.update(Status.SUCCEEDED, datetime.now(zone_info), {"score": 99.9, "benchmark": "test"})
    assert exp_storage.load() == (
        [trial.trial_id],
        [
            {
                "idle": "halt",
                "kernel_sched_latency_ns": "2000000",
                "kernel_sched_migration_cost_ns": "-1",
                "vmSize": "Standard_B4ms",
            }
        ],
        [{"score": "99.9", "benchmark": "test"}],
        [Status.SUCCEEDED],
    )


@pytest.mark.parametrize(("zone_info"), ZONE_INFO)
def test_exp_trial_update_twice(
    exp_storage: Storage.Experiment,
    tunable_groups: TunableGroups,
    zone_info: tzinfo | None,
) -> None:
    """Update the trial status twice and receive an error."""
    trial = exp_storage.new_trial(tunable_groups)
    trial.update(Status.FAILED, datetime.now(zone_info))
    with pytest.raises(RuntimeError):
        trial.update(Status.SUCCEEDED, datetime.now(UTC), {"score": 99.9})


@pytest.mark.parametrize(("zone_info"), ZONE_INFO)
def test_exp_trial_pending_3(
    exp_storage: Storage.Experiment,
    tunable_groups: TunableGroups,
    zone_info: tzinfo | None,
) -> None:
    """
    Start THREE trials, let one succeed, another one fail and keep one not updated.

    Check that one is still pending another one can be loaded into the optimizer.
    """
    score = 99.9

    trial_fail = exp_storage.new_trial(tunable_groups)
    trial_succ = exp_storage.new_trial(tunable_groups)
    trial_pend = exp_storage.new_trial(tunable_groups)

    trial_fail.update(Status.FAILED, datetime.now(zone_info))
    trial_succ.update(Status.SUCCEEDED, datetime.now(zone_info), {"score": score})

    (pending,) = list(exp_storage.pending_trials(datetime.now(UTC), running=True))
    assert pending.trial_id == trial_pend.trial_id

    (trial_ids, configs, scores, status) = exp_storage.load()
    assert trial_ids == [trial_fail.trial_id, trial_succ.trial_id]
    assert len(configs) == 2
    assert scores == [None, {"score": f"{score}"}]
    assert status == [Status.FAILED, Status.SUCCEEDED]
    assert tunable_groups.copy().assign(configs[0]).reset() == trial_fail.tunables
    assert tunable_groups.copy().assign(configs[1]).reset() == trial_succ.tunables


def test_empty_get_longest_prefix_finished_trial_id(
    storage: Storage,
    exp_storage: Storage.Experiment,
) -> None:
    """
    Test that the longest prefix of finished trials is empty when no trials are present.
    """
    assert not storage.experiments[
        exp_storage.experiment_id
    ].trials, "Expected no trials in the experiment."

    # Retrieve the longest prefix of finished trials when no trials are present
    longest_prefix_id = exp_storage.get_longest_prefix_finished_trial_id()

    # Assert that the longest prefix is empty
    assert (
        longest_prefix_id == -1
    ), f"Expected longest prefix to be -1, but got {longest_prefix_id}"


def test_sync_success_get_longest_prefix_finished_trial_id(
    exp_storage: Storage.Experiment,
    tunable_groups: TunableGroups,
) -> None:
    """
    Test that the longest prefix of finished trials is returned correctly when
    all trial are finished.
    """
    timestamp = datetime.now(UTC)
    config = {}
    metrics = {metric: random() for metric in exp_storage.opt_targets}

    # Create several trials
    trials = [exp_storage.new_trial(tunable_groups, config=config) for _ in range(0, 4)]

    # Mark some trials at the beginning and end as finished
    trials[0].update(Status.SUCCEEDED, timestamp + timedelta(minutes=1), metrics=metrics)
    trials[1].update(Status.FAILED, timestamp + timedelta(minutes=2), metrics=metrics)
    trials[2].update(Status.TIMED_OUT, timestamp + timedelta(minutes=3), metrics=metrics)
    trials[3].update(Status.CANCELED, timestamp + timedelta(minutes=4), metrics=metrics)

    # Retrieve the longest prefix of finished trials starting from trial_id 1
    longest_prefix_id = exp_storage.get_longest_prefix_finished_trial_id()

    # Assert that the longest prefix includes only the first three trials
    assert longest_prefix_id == trials[3].trial_id, (
        f"Expected longest prefix to end at trial_id {trials[3].trial_id}, "
        f"but got {longest_prefix_id}"
    )


def test_async_get_longest_prefix_finished_trial_id(
    exp_storage: Storage.Experiment,
    tunable_groups: TunableGroups,
) -> None:
    """
    Test that the longest prefix of finished trials is returned correctly when
    trial finish out of order.
    """
    timestamp = datetime.now(UTC)
    config = {}
    metrics = {metric: random() for metric in exp_storage.opt_targets}

    # Create several trials
    trials = [exp_storage.new_trial(tunable_groups, config=config) for _ in range(0, 10)]

    # Mark some trials at the beginning and end as finished
    trials[0].update(Status.SUCCEEDED, timestamp + timedelta(minutes=1), metrics=metrics)
    trials[1].update(Status.FAILED, timestamp + timedelta(minutes=2), metrics=metrics)
    trials[2].update(Status.TIMED_OUT, timestamp + timedelta(minutes=3), metrics=metrics)
    trials[3].update(Status.CANCELED, timestamp + timedelta(minutes=4), metrics=metrics)
    # Leave trials[3] to trials[7] as PENDING
    trials[9].update(Status.SUCCEEDED, timestamp + timedelta(minutes=5), metrics=metrics)

    # Retrieve the longest prefix of finished trials starting from trial_id 1
    longest_prefix_id = exp_storage.get_longest_prefix_finished_trial_id()

    # Assert that the longest prefix includes only the first three trials
    assert longest_prefix_id == trials[3].trial_id, (
        f"Expected longest prefix to end at trial_id {trials[3].trial_id}, "
        f"but got {longest_prefix_id}"
    )


# TODO: Can we simplify this to use something like SyncScheduler and
# bulk_register_completed_trials?
def test_exp_load_async(
    exp_storage: Storage.Experiment,
    tunable_groups: TunableGroups,
) -> None:
    """
    Test the `omit_registered_trial_ids` argument of the `Experiment.load()` method.

    Create several trials with mixed statuses (PENDING and completed).
    Verify that completed trials included in a local set of registered configs
    are omitted from the `load` operation.
    """
    # pylint: disable=too-many-locals,too-many-statements

    last_trial_id = exp_storage.get_longest_prefix_finished_trial_id()
    assert last_trial_id == -1, "Expected no trials in the experiment."
    registered_trial_ids: set[int] = set()

    # Load trials, omitting registered ones
    trial_ids, configs, scores, status = exp_storage.load(
        last_trial_id=last_trial_id,
        omit_registered_trial_ids=registered_trial_ids,
    )

    assert trial_ids == []
    assert configs == []
    assert scores == []
    assert status == []

    # Create trials with mixed statuses
    trial_1_success = exp_storage.new_trial(tunable_groups)
    trial_2_failed = exp_storage.new_trial(tunable_groups)
    trial_3_pending = exp_storage.new_trial(tunable_groups)
    trial_4_timedout = exp_storage.new_trial(tunable_groups)
    trial_5_pending = exp_storage.new_trial(tunable_groups)

    # Update statuses for completed trials
    trial_1_success.update(Status.SUCCEEDED, datetime.now(UTC), {"score": 95.0})
    trial_2_failed.update(Status.FAILED, datetime.now(UTC), {"score": -1})
    trial_4_timedout.update(Status.TIMED_OUT, datetime.now(UTC), {"score": -1})

    # Now evaluate some different sequences of loading trials by simulating what
    # we expect a Scheduler to do.
    # See Also: Scheduler.add_new_optimizer_suggestions()

    trial_ids, configs, scores, status = exp_storage.load(
        last_trial_id=last_trial_id,
        omit_registered_trial_ids=registered_trial_ids,
    )

    # Verify that all completed trials are returned.
    completed_trials = [
        trial_1_success,
        trial_2_failed,
        trial_4_timedout,
    ]
    assert trial_ids == [trial.trial_id for trial in completed_trials]
    assert len(configs) == len(completed_trials)
    assert status == [trial.status for trial in completed_trials]

    last_trial_id = exp_storage.get_longest_prefix_finished_trial_id()
    assert last_trial_id == trial_2_failed.trial_id, (
        f"Expected longest prefix to end at trial_id {trial_2_failed.trial_id}, "
        f"but got {last_trial_id}"
    )
    registered_trial_ids |= {completed_trial.trial_id for completed_trial in completed_trials}
    registered_trial_ids = {i for i in registered_trial_ids if i > last_trial_id}

    # Create some more trials and update their statuses.
    # Note: we are leaving some trials in the middle in the PENDING state.
    trial_6_canceled = exp_storage.new_trial(tunable_groups)
    trial_7_success2 = exp_storage.new_trial(tunable_groups)
    trial_6_canceled.update(Status.CANCELED, datetime.now(UTC), {"score": -1})
    trial_7_success2.update(Status.SUCCEEDED, datetime.now(UTC), {"score": 90.0})

    # Load trials, omitting registered ones
    trial_ids, configs, scores, status = exp_storage.load(
        last_trial_id=last_trial_id,
        omit_registered_trial_ids=registered_trial_ids,
    )
    # Verify that only unregistered completed trials are returned
    completed_trials = [
        trial_6_canceled,
        trial_7_success2,
    ]
    assert trial_ids == [trial.trial_id for trial in completed_trials]
    assert len(configs) == len(completed_trials)
    assert status == [trial.status for trial in completed_trials]

    # Update our tracking of registered trials
    last_trial_id = exp_storage.get_longest_prefix_finished_trial_id()
    # Should still be the same as before since we haven't adjusted the PENDING
    # trials at the beginning yet.
    assert last_trial_id == trial_2_failed.trial_id, (
        f"Expected longest prefix to end at trial_id {trial_2_failed.trial_id}, "
        f"but got {last_trial_id}"
    )
    registered_trial_ids |= {completed_trial.trial_id for completed_trial in completed_trials}
    registered_trial_ids = {i for i in registered_trial_ids if i > last_trial_id}

    trial_ids, configs, scores, status = exp_storage.load(
        last_trial_id=last_trial_id,
        omit_registered_trial_ids=registered_trial_ids,
    )

    # Verify that only unregistered completed trials are returned
    completed_trials = []
    assert trial_ids == [trial.trial_id for trial in completed_trials]
    assert len(configs) == len(completed_trials)
    assert status == [trial.status for trial in completed_trials]

    # Now update the PENDING trials to be TIMED_OUT.
    trial_3_pending.update(Status.TIMED_OUT, datetime.now(UTC), {"score": -1})

    # Load trials, omitting registered ones
    trial_ids, configs, scores, status = exp_storage.load(
        last_trial_id=last_trial_id,
        omit_registered_trial_ids=registered_trial_ids,
    )

    # Verify that only unregistered completed trials are returned
    completed_trials = [
        trial_3_pending,
    ]
    assert trial_ids == [trial.trial_id for trial in completed_trials]
    assert len(configs) == len(completed_trials)
    assert status == [trial.status for trial in completed_trials]

    # Update our tracking of registered trials
    last_trial_id = exp_storage.get_longest_prefix_finished_trial_id()
    assert last_trial_id == trial_4_timedout.trial_id, (
        f"Expected longest prefix to end at trial_id {trial_4_timedout.trial_id}, "
        f"but got {last_trial_id}"
    )
    registered_trial_ids |= {completed_trial.trial_id for completed_trial in completed_trials}
    registered_trial_ids = {i for i in registered_trial_ids if i > last_trial_id}

    # Load trials, omitting registered ones
    trial_ids, configs, scores, status = exp_storage.load(
        last_trial_id=last_trial_id,
        omit_registered_trial_ids=registered_trial_ids,
    )
    # Verify that only unregistered completed trials are returned
    completed_trials = []
    assert trial_ids == [trial.trial_id for trial in completed_trials]
    assert len(configs) == len(completed_trials)
    assert status == [trial.status for trial in completed_trials]
    # And that the longest prefix is still the same.
    assert last_trial_id == trial_4_timedout.trial_id, (
        f"Expected longest prefix to end at trial_id {trial_4_timedout.trial_id}, "
        f"but got {last_trial_id}"
    )

    # Mark the last trial as finished.
    trial_5_pending.update(Status.SUCCEEDED, datetime.now(UTC), {"score": 95.0})
    # Load trials, omitting registered ones
    trial_ids, configs, scores, status = exp_storage.load(
        last_trial_id=last_trial_id,
        omit_registered_trial_ids=registered_trial_ids,
    )
    # Verify that only unregistered completed trials are returned
    completed_trials = [
        trial_5_pending,
    ]
    assert trial_ids == [trial.trial_id for trial in completed_trials]
    assert len(configs) == len(completed_trials)
    assert status == [trial.status for trial in completed_trials]
    # And that the longest prefix is now the last trial.
    last_trial_id = exp_storage.get_longest_prefix_finished_trial_id()
    assert last_trial_id == trial_7_success2.trial_id, (
        f"Expected longest prefix to end at trial_id {trial_7_success2.trial_id}, "
        f"but got {last_trial_id}"
    )
    registered_trial_ids |= {completed_trial.trial_id for completed_trial in completed_trials}
    registered_trial_ids = {i for i in registered_trial_ids if i > last_trial_id}
    assert registered_trial_ids == set()
