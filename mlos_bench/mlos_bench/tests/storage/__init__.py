#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Test fixtures for mlos_bench storage.
"""

from datetime import datetime

import pytest

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.storage.sql.storage import SqlStorage
from mlos_bench.tunables.tunable_groups import TunableGroups

# pylint: disable=redefined-outer-name


@pytest.fixture
def storage_memory_sql() -> SqlStorage:
    """
    Test fixture for in-memory SQLite3 storage.
    """
    return SqlStorage(
        service=None,
        config={
            "drivername": "sqlite",
            "database": ":memory:",
        }
    )


@pytest.fixture
def exp_storage_memory_sql(storage_memory_sql: Storage, tunable_groups: TunableGroups) -> SqlStorage.Experiment:
    """
    Test fixture for Experiment using in-memory SQLite3 storage.
    """
    opt_target = "score"
    opt_direction = "min"
    with storage_memory_sql.experiment(
        experiment_id="Test-001",
        trial_id=1,
        root_env_config="environment.jsonc",
        description="pytest experiment",
        tunables=tunable_groups,
        opt_target=opt_target,
        opt_direction=opt_direction,
    ) as exp:
        # Add some trials to that experiment.
        # Note: these all use the same values for now.
        for i in range(1, 3):
            trial = exp.new_trial(tunables=exp.tunables.copy(), config={
                "opt_target": opt_target,
                "opt_direction": opt_direction,
                "trial_number": i,
            })
            trial.update_telemetry(status=Status.RUNNING, metrics=[
                (datetime.utcnow(), "some-metric", 1.0),
            ])
            trial.update(Status.SUCCEEDED, datetime.utcnow(), metrics={
                "score": 1.0,
            })
        return exp


@pytest.fixture
def exp_data(storage_memory_sql: Storage, exp_storage_memory_sql: Storage.Experiment) -> ExperimentData:
    """
    Test fixture for ExperimentData.
    """
    return storage_memory_sql.experiments[exp_storage_memory_sql.experiment_id]
