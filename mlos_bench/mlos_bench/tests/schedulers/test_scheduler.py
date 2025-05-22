#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for :py:class:`mlos_bench.schedulers` and their internals."""

import sys
from unittest.mock import patch

import pytest

import mlos_bench.tests.optimizers.fixtures as optimizers_fixtures
import mlos_bench.tests.storage.sql.fixtures as sql_storage_fixtures
from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.schedulers.trial_runner import TrialRunner
from mlos_bench.storage.sql.storage import SqlStorage
from mlos_core.tests import get_all_concrete_subclasses

mock_opt = optimizers_fixtures.mock_opt
sqlite_storage = sql_storage_fixtures.sqlite_storage

# pylint: disable=redefined-outer-name


def create_scheduler(
    scheduler_type: type[Scheduler],
    trial_runners: list[TrialRunner],
    mock_opt: MockOptimizer,
    sqlite_storage: SqlStorage,
    global_config: dict,
) -> Scheduler:
    """Create a Scheduler instance using trial_runners, mock_opt, and sqlite_storage
    fixtures.
    """

    env = trial_runners[0].environment
    assert isinstance(env, MockEnv), "Environment is not a MockEnv instance."
    max_trials = max(trial_id for trial_id in env.mock_trial_data.keys())
    max_trials = min(max_trials, mock_opt.max_suggestions)

    global_config["experiment_id"] = f"Test{scheduler_type.__name__}Experiment"

    return scheduler_type(
        config={
            "max_trials": max_trials,
        },
        global_config=global_config,
        trial_runners=trial_runners,
        optimizer=mock_opt,
        storage=sqlite_storage,
        root_env_config="",
    )


scheduler_classes = get_all_concrete_subclasses(
    Scheduler,  # type: ignore[type-abstract]
    pkg_name="mlos_bench",
)
assert scheduler_classes, "No Scheduler classes found in mlos_bench."


@pytest.mark.parametrize(
    "scheduler_class",
    scheduler_classes,
)
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Skipping test on Windows - SQLite storage is not accessible in parallel tests there.",
)
def test_scheduler(
    scheduler_class: type[Scheduler],
    trial_runners: list[TrialRunner],
    mock_opt: MockOptimizer,
    sqlite_storage: SqlStorage,
    global_config: dict,
) -> None:
    """
    Full integration test for Scheduler: runs trials, checks storage, optimizer
    registration, and internal bookkeeping.
    """
    # pylint: disable=too-many-locals

    # Create the scheduler.
    scheduler = create_scheduler(
        scheduler_class,
        trial_runners,
        mock_opt,
        sqlite_storage,
        global_config,
    )

    root_env = scheduler.root_environment
    assert isinstance(root_env, MockEnv), "Root environment is not a MockEnv instance."
    mock_trial_data = root_env.mock_trial_data

    # Run the scheduler
    with scheduler:
        scheduler.start()
        scheduler.teardown()

    # Now check the results.
    # TODO:
    # Check the overall results:
    # 1. Check the results in storage.
    # 2. Check the optimizer registration.
    # 3. Check the bookkeeping for ran_trials.
    # 4. Check the bookkeeping for add_new_optimizer_suggestions and _last_trial_id.
    #    This last part may require patching and intercepting during the start()
    #    loop to validate in-progress book keeping instead of just overall.
