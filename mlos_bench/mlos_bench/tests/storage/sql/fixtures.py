#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Test fixtures for mlos_bench storage."""

from datetime import datetime
from random import random
from random import seed as rand_seed
from typing import Generator, Optional

import pytest
from pytz import UTC

from mlos_bench.environments.status import Status
from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.storage.sql.storage import SqlStorage
from mlos_bench.tests import SEED
from mlos_bench.tests.storage import CONFIG_COUNT, CONFIG_TRIAL_REPEAT_COUNT
from mlos_bench.tunables.tunable_groups import TunableGroups

# pylint: disable=redefined-outer-name


@pytest.fixture
def storage() -> SqlStorage:
    """Test fixture for in-memory SQLite3 storage."""
    return SqlStorage(
        service=None,
        config={
            "drivername": "sqlite",
            "database": ":memory:",
            # "database": "mlos_bench.pytest.db",
        },
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
    with storage.experiment(
        experiment_id="Test-001",
        trial_id=1,
        root_env_config="environment.jsonc",
        description="pytest experiment",
        tunables=tunable_groups,
        opt_targets={"score": "min"},
    ) as exp:
        yield exp
    # pylint: disable=protected-access
    assert not exp._in_context


@pytest.fixture
def exp_no_tunables_storage(
    storage: SqlStorage,
) -> Generator[SqlStorage.Experiment, None, None]:
    """
    Test fixture for Experiment using in-memory SQLite3 storage.

    Note: It has already entered the context upon return.
    """
    empty_config: dict = {}
    with storage.experiment(
        experiment_id="Test-003",
        trial_id=1,
        root_env_config="environment.jsonc",
        description="pytest experiment - no tunables",
        tunables=TunableGroups(empty_config),
        opt_targets={"score": "min"},
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
    Test fixture for an Experiment with mixed numerics tunables using in-memory SQLite3
    storage.

    Note: It has already entered the context upon return.
    """
    with storage.experiment(
        experiment_id="Test-002",
        trial_id=1,
        root_env_config="dne.jsonc",
        description="pytest experiment",
        tunables=mixed_numerics_tunable_groups,
        opt_targets={"score": "min"},
    ) as exp:
        yield exp
    # pylint: disable=protected-access
    assert not exp._in_context


def _dummy_run_exp(
    exp: SqlStorage.Experiment,
    tunable_name: Optional[str],
) -> SqlStorage.Experiment:
    """Generates data by doing a simulated run of the given experiment."""
    # Add some trials to that experiment.
    # Note: we're just fabricating some made up function for the ML libraries to try and learn.
    base_score = 10.0
    if tunable_name:
        tunable = exp.tunables.get_tunable(tunable_name)[0]
        assert isinstance(tunable.default, int)
        (tunable_min, tunable_max) = tunable.range
        tunable_range = tunable_max - tunable_min
    rand_seed(SEED)
    opt = MockOptimizer(
        tunables=exp.tunables,
        config={
            "seed": SEED,
            # This should be the default, so we leave it omitted for now to test the default.
            # But the test logic relies on this (e.g., trial 1 is config 1 is the
            # default values for the tunable params)
            # "start_with_defaults": True,
        },
    )
    assert opt.start_with_defaults
    for config_i in range(CONFIG_COUNT):
        tunables = opt.suggest()
        for repeat_j in range(CONFIG_TRIAL_REPEAT_COUNT):
            trial = exp.new_trial(
                tunables=tunables.copy(),
                config={
                    "trial_number": config_i * CONFIG_TRIAL_REPEAT_COUNT + repeat_j + 1,
                    **{
                        f"opt_{key}_{i}": val
                        for (i, opt_target) in enumerate(exp.opt_targets.items())
                        for (key, val) in zip(["target", "direction"], opt_target)
                    },
                },
            )
            if exp.tunables:
                assert trial.tunable_config_id == config_i + 1
            else:
                assert trial.tunable_config_id == 1
            if tunable_name:
                tunable_value = float(tunables.get_tunable(tunable_name)[0].numerical_value)
                tunable_value_norm = base_score * (tunable_value - tunable_min) / tunable_range
            else:
                tunable_value_norm = 0
            timestamp = datetime.now(UTC)
            trial.update_telemetry(
                status=Status.RUNNING,
                timestamp=timestamp,
                metrics=[
                    (timestamp, "some-metric", tunable_value_norm + random() / 100),
                ],
            )
            trial.update(
                Status.SUCCEEDED,
                timestamp,
                metrics={
                    # Give some variance on the score.
                    # And some influence from the tunable value.
                    "score": tunable_value_norm
                    + random() / 100
                },
            )
    return exp


@pytest.fixture
def exp_storage_with_trials(exp_storage: SqlStorage.Experiment) -> SqlStorage.Experiment:
    """Test fixture for Experiment using in-memory SQLite3 storage."""
    return _dummy_run_exp(exp_storage, tunable_name="kernel_sched_latency_ns")


@pytest.fixture
def exp_no_tunables_storage_with_trials(
    exp_no_tunables_storage: SqlStorage.Experiment,
) -> SqlStorage.Experiment:
    """Test fixture for Experiment using in-memory SQLite3 storage."""
    assert not exp_no_tunables_storage.tunables
    return _dummy_run_exp(exp_no_tunables_storage, tunable_name=None)


@pytest.fixture
def mixed_numerics_exp_storage_with_trials(
    mixed_numerics_exp_storage: SqlStorage.Experiment,
) -> SqlStorage.Experiment:
    """Test fixture for Experiment using in-memory SQLite3 storage."""
    tunable = next(iter(mixed_numerics_exp_storage.tunables))[0]
    return _dummy_run_exp(mixed_numerics_exp_storage, tunable_name=tunable.name)


@pytest.fixture
def exp_data(
    storage: SqlStorage,
    exp_storage_with_trials: SqlStorage.Experiment,
) -> ExperimentData:
    """Test fixture for ExperimentData."""
    return storage.experiments[exp_storage_with_trials.experiment_id]


@pytest.fixture
def exp_no_tunables_data(
    storage: SqlStorage,
    exp_no_tunables_storage_with_trials: SqlStorage.Experiment,
) -> ExperimentData:
    """Test fixture for ExperimentData with no tunable configs."""
    return storage.experiments[exp_no_tunables_storage_with_trials.experiment_id]


@pytest.fixture
def mixed_numerics_exp_data(
    storage: SqlStorage,
    mixed_numerics_exp_storage_with_trials: SqlStorage.Experiment,
) -> ExperimentData:
    """Test fixture for ExperimentData with mixed numerical tunable types."""
    return storage.experiments[mixed_numerics_exp_storage_with_trials.experiment_id]
