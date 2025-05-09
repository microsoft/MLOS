
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""
Test pickling and unpickling of Storage, and restoring Experiment and Trial by id.
"""
import os
import pickle
import tempfile
from typing import Literal

from mlos_bench.storage.sql.storage import SqlStorage
from mlos_bench.tunables.tunable_groups import TunableGroups

def test_storage_pickle_restore_experiment_and_trial(tunable_groups: TunableGroups) -> None:
    # pylint: disable=too-many-locals
    """Check that we can pickle and unpickle the Storage object, and restore
    Experiment and Trial by id.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "mlos_bench.sqlite")
        config = {
            "drivername": "sqlite",
            "database": db_path,
            "lazy_schema_create": False,
        }
        storage = SqlStorage(config)
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

        # Pickle and unpickle the Storage object
        pickled = pickle.dumps(storage)
        restored_storage = pickle.loads(pickled)
        assert isinstance(restored_storage, SqlStorage)

        # Restore the Experiment from storage by id
        restored_experiment = restored_storage.get_experiment_by_id(
            experiment_id=experiment.experiment_id,
            tunables=tunable_groups,
            opt_targets=opt_targets,
        )
        assert restored_experiment is not None
        assert restored_experiment.experiment_id == experiment.experiment_id
        assert restored_experiment.description == experiment.description
        assert restored_experiment.root_env_config == experiment.root_env_config
        assert restored_experiment.opt_targets == experiment.opt_targets

        # Restore the Trial from storage by id
        with restored_experiment:
            restored_trial = restored_experiment.get_trial_by_id(trial_id_created)
            assert restored_trial is not None
            assert restored_trial.trial_id == trial.trial_id
            assert restored_trial.experiment_id == trial.experiment_id
            assert restored_trial.tunables == trial.tunables
