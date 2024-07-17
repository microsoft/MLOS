#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for the storage subsystem."""
from datetime import datetime, tzinfo
from typing import Optional

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
    zone_info: Optional[tzinfo],
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
    zone_info: Optional[tzinfo],
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
    zone_info: Optional[tzinfo],
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
    zone_info: Optional[tzinfo],
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
    zone_info: Optional[tzinfo],
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
    zone_info: Optional[tzinfo],
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
    zone_info: Optional[tzinfo],
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
