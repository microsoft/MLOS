#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Test pickling and unpickling of Storage, and restoring Experiment and Trial by id."""
import pickle
import sys
from datetime import datetime
from typing import Literal

import pytest
from pytest_lazy_fixtures.lazy_fixture import lf as lazy_fixture
from pytz import UTC

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tests import DOCKER
from mlos_bench.tunables.tunable_groups import TunableGroups

docker_dbms_fixtures = []
if DOCKER:
    docker_dbms_fixtures = [
        lazy_fixture("mysql_storage"),
        lazy_fixture("postgres_storage"),
    ]


# TODO: When we introduce ParallelTrialScheduler warn at config startup time
# that it is incompatible with sqlite storage on Windows.
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows doesn't support multiple processes accessing the same file.",
)
@pytest.mark.parametrize(
    "persistent_storage",
    [
        # TODO: Improve this test to support non-sql backends eventually as well.
        lazy_fixture("sqlite_storage"),
        *docker_dbms_fixtures,
    ],
)
def test_storage_pickle_restore_experiment_and_trial(
    persistent_storage: Storage,
    tunable_groups: TunableGroups,
) -> None:
    """Check that we can pickle and unpickle the Storage object, and restore Experiment
    and Trial by id.
    """
    storage = persistent_storage
    storage_class = storage.__class__
    assert issubclass(storage_class, Storage)
    assert storage_class != Storage
    # Create an Experiment and a Trial
    opt_targets: dict[str, Literal["min", "max"]] = {"metric": "min"}
    experiment = storage.experiment(
        experiment_id="experiment_id",
        trial_id=0,
        root_env_config="dummy_env.json",
        description="Pickle test experiment",
        tunables=tunable_groups,
        opt_targets=opt_targets,
    )
    with experiment:
        trial = experiment.new_trial(tunable_groups)
        trial_id_created = trial.trial_id
        trial.set_trial_runner(1)
        trial.update(Status.RUNNING, datetime.now(UTC))

    # Pickle and unpickle the Storage object
    pickled = pickle.dumps(storage)
    restored_storage = pickle.loads(pickled)
    assert isinstance(restored_storage, storage_class)

    # Restore the Experiment from storage by id and check that it matches the original
    restored_experiment = restored_storage.get_experiment_by_id(
        experiment_id=experiment.experiment_id,
        tunables=tunable_groups,
        opt_targets=opt_targets,
    )
    assert restored_experiment is not None
    assert restored_experiment is not experiment
    assert restored_experiment.experiment_id == experiment.experiment_id
    assert restored_experiment.description == experiment.description
    assert restored_experiment.root_env_config == experiment.root_env_config
    assert restored_experiment.tunables == experiment.tunables
    assert restored_experiment.opt_targets == experiment.opt_targets
    with restored_experiment:
        # trial_id should have been restored during __enter__
        assert restored_experiment.trial_id == experiment.trial_id

    # Restore the Trial from storage by id and check that it matches the original
    restored_trial = restored_experiment.get_trial_by_id(trial_id_created)
    assert restored_trial is not None
    assert restored_trial is not trial
    assert restored_trial.trial_id == trial.trial_id
    assert restored_trial.experiment_id == trial.experiment_id
    assert restored_trial.tunables == trial.tunables
    assert restored_trial.status == trial.status
    assert restored_trial.config() == trial.config()
    assert restored_trial.trial_runner_id == trial.trial_runner_id
