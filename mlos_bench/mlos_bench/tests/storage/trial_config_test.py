#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for saving and retrieving additional parameters of pending trials."""
from datetime import datetime
from typing import Any

import pytest
from pytz import UTC

from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_exp_trial_pending(exp_storage: Storage.Experiment, tunable_groups: TunableGroups) -> None:
    """Schedule a trial and check that it is pending and has the right configuration."""
    config = {"location": "westus2", "num_repeats": 100}
    trial = exp_storage.new_trial(tunable_groups, config=config)
    (pending,) = list(exp_storage.pending_trials(datetime.now(UTC), running=True))
    assert pending.trial_id == trial.trial_id
    assert pending.tunables == tunable_groups
    assert pending.config() == {
        "location": "westus2",
        "num_repeats": "100",
        "experiment_id": "Test-001",
        "trial_id": trial.trial_id,
    }


def test_add_new_trial_config_data(
    storage: Storage,
    exp_storage: Storage.Experiment,
    tunable_groups: TunableGroups,
) -> None:
    """Create a trial and check that adding new data to the config is allowed."""
    config = {"location": "westus2", "num_repeats": 100}
    trial = exp_storage.new_trial(tunable_groups, config=config)
    new_config = {"new_key": "new_value"}
    trial.add_new_config_data(new_config)
    trial_data = storage.experiments[exp_storage.experiment_id].trials[trial.trial_id]
    assert trial_data.metadata_dict == {
        **config,
        **new_config,
    }


def test_add_bad_new_trial_config_data(
    storage: Storage,
    exp_storage: Storage.Experiment,
    tunable_groups: TunableGroups,
) -> None:
    """Create a trial and check that adding repeated data to the config is
    disallowed.
    """
    config = {"location": "westus2", "num_repeats": 100}
    trial = exp_storage.new_trial(tunable_groups, config=config)
    new_config = {"location": "eastus2"}
    with pytest.raises(ValueError):
        trial.add_new_config_data(new_config)
    trial_data = storage.experiments[exp_storage.experiment_id].trials[trial.trial_id]
    assert trial_data.metadata_dict == {
        **config,
    }


def test_exp_trial_configs(exp_storage: Storage.Experiment, tunable_groups: TunableGroups) -> None:
    """Start multiple trials with two different configs and check that we store only two
    config objects in the DB.
    """
    config1 = tunable_groups.copy().assign({"idle": "mwait"})
    trials1 = [
        exp_storage.new_trial(config1),
        exp_storage.new_trial(config1),
        exp_storage.new_trial(config1.copy()),  # Same values, different instance
    ]
    assert trials1[0].tunable_config_id == trials1[1].tunable_config_id
    assert trials1[0].tunable_config_id == trials1[2].tunable_config_id

    config2 = tunable_groups.copy().assign({"idle": "halt"})
    trials2 = [
        exp_storage.new_trial(config2),
        exp_storage.new_trial(config2),
        exp_storage.new_trial(config2.copy()),  # Same values, different instance
    ]
    assert trials2[0].tunable_config_id == trials2[1].tunable_config_id
    assert trials2[0].tunable_config_id == trials2[2].tunable_config_id

    assert trials1[0].tunable_config_id != trials2[0].tunable_config_id

    pending_ids = [
        pending.tunable_config_id
        for pending in exp_storage.pending_trials(datetime.now(UTC), running=True)
    ]
    assert len(pending_ids) == 6
    assert len(set(pending_ids)) == 2
    assert set(pending_ids) == {trials1[0].tunable_config_id, trials2[0].tunable_config_id}


def test_exp_trial_no_config(exp_no_tunables_storage: Storage.Experiment) -> None:
    """Schedule a trial that has an empty tunable groups config."""
    empty_config: dict = {}
    tunable_groups = TunableGroups(config=empty_config)
    trial = exp_no_tunables_storage.new_trial(tunable_groups, config=empty_config)
    (pending,) = exp_no_tunables_storage.pending_trials(datetime.now(UTC), running=True)
    assert pending.trial_id == trial.trial_id
    assert pending.tunables == tunable_groups
    assert pending.config() == {
        "experiment_id": "Test-003",
        "trial_id": trial.trial_id,
    }


@pytest.mark.parametrize(
    "bad_config",
    [
        {
            "obj": object(),
        },
        {
            "callable": lambda x: x,
        },
        {
            "nested": {
                "callable": lambda x: x,
            },
        },
    ],
)
def test_exp_trial_non_serializable_config(
    exp_no_tunables_storage: Storage.Experiment,
    bad_config: dict[str, Any],
) -> None:
    """Tests that a trial with a non-serializable config is rejected."""
    empty_config: dict = {}
    tunable_groups = TunableGroups(config=empty_config)
    with pytest.raises(ValueError):
        exp_no_tunables_storage.new_trial(tunable_groups, config=bad_config)
