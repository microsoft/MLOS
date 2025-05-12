#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Test pickling and unpickling of Storage, and restoring Experiment and Trial by id."""
import json
import os
import pickle
import sys
import tempfile
from datetime import datetime
from typing import Literal

import pytest
from pytz import UTC

from mlos_bench.environments.status import Status
from mlos_bench.storage.sql.storage import SqlStorage
from mlos_bench.storage.storage_factory import from_config
from mlos_bench.tunables.tunable_groups import TunableGroups


# TODO: When we introduce ParallelTrialScheduler warn at config startup time
# that it is incompatible with sqlite storage on Windows.
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows doesn't support multiple processes accessing the same file.",
)
def test_storage_pickle_restore_experiment_and_trial(tunable_groups: TunableGroups) -> None:
    """Check that we can pickle and unpickle the Storage object, and restore Experiment
    and Trial by id.
    """
    # pylint: disable=too-many-locals
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "mlos_bench.sqlite")
        config_str = json.dumps(
            {
                "class": "mlos_bench.storage.sql.storage.SqlStorage",
                "config": {
                    "drivername": "sqlite",
                    "database": db_path,
                    "lazy_schema_create": False,
                },
            }
        )

        storage = from_config(config_str)
        storage.update_schema()

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
        assert isinstance(restored_storage, SqlStorage)

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
