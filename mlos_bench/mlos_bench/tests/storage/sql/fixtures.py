#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Test fixtures for mlos_bench storage.
"""

from datetime import datetime
from random import random, seed as rand_seed
from typing import Generator

import pytest

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.storage.sql.storage import SqlStorage
from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.tunables.tunable_groups import TunableGroups

from mlos_bench.tests import SEED
from mlos_bench.tests.storage import CONFIG_COUNT, CONFIG_TRIAL_REPEAT_COUNT

# pylint: disable=redefined-outer-name


@pytest.fixture
def storage() -> SqlStorage:
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
def exp_storage(
    storage: SqlStorage,
    tunable_groups: TunableGroups,
) -> Generator[SqlStorage.Experiment, None, None]:
    """
    Test fixture for Experiment using in-memory SQLite3 storage.
    Note: It has already entered the context upon return.
    """
    opt_target = "score"
    opt_direction = "min"
    with storage.experiment(
        experiment_id="Test-001",
        trial_id=1,
        root_env_config="environment.jsonc",
        description="pytest experiment",
        tunables=tunable_groups,
        opt_target=opt_target,
        opt_direction=opt_direction,
    ) as exp:
        yield exp
    # pylint: disable=protected-access
    assert not exp._in_context


@pytest.fixture
def mixed_numerics_exp_storage(
    storage: SqlStorage,
    mixed_numerics_tunable_groups: TunableGroups,
) -> Generator[SqlStorage.Experiment, None, None]:
    """
    Test fixture for an Experiment with mixed numerics tunables using in-memory SQLite3 storage.
    Note: It has already entered the context upon return.
    """
    opt_target = "score"
    opt_direction = "min"
    with storage.experiment(
        experiment_id="Test-002",
        trial_id=1,
        root_env_config="dne.jsonc",
        description="pytest experiment",
        tunables=mixed_numerics_tunable_groups,
        opt_target=opt_target,
        opt_direction=opt_direction,
    ) as exp:
        yield exp
    # pylint: disable=protected-access
    assert not exp._in_context


def _dummy_run_exp(exp: SqlStorage.Experiment, tunable_name: str) -> SqlStorage.Experiment:
    """
    Generates data by doing a simulated run of the given experiment.
    """
    # Add some trials to that experiment.
    # Note: we're just fabricating some made up function for the ML libraries to try and learn.
    base_score = 10.0
    tunable = exp.tunables.get_tunable(tunable_name)[0]
    tunable_default = tunable.default
    assert isinstance(tunable_default, int)
    tunable_min = tunable.range[0]
    tunable_max = tunable.range[1]
    tunable_range = tunable_max - tunable_min
    rand_seed(SEED)
    opt = MockOptimizer(tunables=exp.tunables, config={
        "seed": SEED,
        # This should be the default, so we leave it omitted for now to test the default.
        # But the test logic relies on this (e.g., trial 1 is config 1 is the default values for the tunable params)
        # "start_with_defaults": True,
    })
    assert opt.start_with_defaults
    for config_i in range(CONFIG_COUNT):
        tunables = opt.suggest()
        for repeat_j in range(CONFIG_TRIAL_REPEAT_COUNT):
            trial = exp.new_trial(tunables=tunables.copy(), config={
                "opt_target": exp.opt_target,
                "opt_direction": exp.opt_direction,
                "trial_number": config_i * CONFIG_TRIAL_REPEAT_COUNT + repeat_j + 1,
            })
            assert trial.tunable_config_id == config_i + 1
            tunable_value = float(tunables.get_tunable(tunable_name)[0].numerical_value)
            tunable_value_norm = base_score * (tunable_value - tunable_min) / tunable_range
            timestamp = datetime.utcnow()
            trial.update_telemetry(status=Status.RUNNING, timestamp=timestamp, metrics=[
                (timestamp, "some-metric", tunable_value_norm + random() / 100),
            ])
            trial.update(Status.SUCCEEDED, timestamp, metrics={
                # Give some variance on the score.
                # And some influence from the tunable value.
                "score": tunable_value_norm + random() / 100
            })
    return exp


@pytest.fixture
def exp_storage_with_trials(exp_storage: SqlStorage.Experiment) -> SqlStorage.Experiment:
    """
    Test fixture for Experiment using in-memory SQLite3 storage.
    """
    return _dummy_run_exp(exp_storage, tunable_name="kernel_sched_latency_ns")


@pytest.fixture
def mixed_numerics_exp_storage_with_trials(mixed_numerics_exp_storage: SqlStorage.Experiment) -> SqlStorage.Experiment:
    """
    Test fixture for Experiment using in-memory SQLite3 storage.
    """
    tunable = next(iter(mixed_numerics_exp_storage.tunables))[0]
    return _dummy_run_exp(mixed_numerics_exp_storage, tunable_name=tunable.name)


@pytest.fixture
def exp_data(storage: SqlStorage, exp_storage_with_trials: SqlStorage.Experiment) -> ExperimentData:
    """
    Test fixture for ExperimentData.
    """
    return storage.experiments[exp_storage_with_trials.experiment_id]


@pytest.fixture
def mixed_numerics_exp_data(storage: SqlStorage, mixed_numerics_exp_storage_with_trials: SqlStorage.Experiment) -> ExperimentData:
    """
    Test fixture for ExperimentData with mixed numerical tunable types.
    """
    return storage.experiments[mixed_numerics_exp_storage_with_trials.experiment_id]
