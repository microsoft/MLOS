#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for :py:class:`mlos_bench.schedulers` and their internals.
"""

import pytest
import unittest.mock
import sys

from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.storage.sql.storage import SqlStorage
from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.schedulers.sync_scheduler import SyncScheduler
from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.schedulers.trial_runner import TrialRunner
import mlos_bench.tests.optimizers.fixtures as optimizers_fixtures

mock_opt = optimizers_fixtures.mock_opt

# pylint: disable=redefined-outer-name


def create_scheduler(
    scheduler_type: type[Scheduler],
    trial_runners: list[TrialRunner],
    mock_opt: MockOptimizer,
    sqlite_storage: SqlStorage,
) -> Scheduler:
    """Create a Scheduler instance using trial_runners, mock_opt, and sqlite_storage."""
    return scheduler_type(
        config={},
        global_config={},
        trial_runners=trial_runners,
        optimizer=mock_opt,
        storage=sqlite_storage,
        root_env_config="",
    )


@pytest.mark.parametrize(
    "scheduler_class",
    [
        SyncScheduler,
    ],
)
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Skipping test on Windows - SQLite storage is not accessible in parallel tests there.",
)
def test_scheduler(
    scheduler_class: type[Scheduler],
    # fixtures:
    trial_runners: list[TrialRunner],
    mock_opt: MockOptimizer,
    sqlite_storage: SqlStorage,
) -> None:
    """
    Test the creation of a SyncScheduler instance.
    """
    scheduler = create_scheduler(
        scheduler_class,
        trial_runners,
        mock_opt,
        sqlite_storage,
    )
    assert isinstance(scheduler, scheduler_class)
    assert isinstance(scheduler.trial_runners, list)
    assert len(scheduler.trial_runners) == len(trial_runners)
    assert isinstance(scheduler.optimizer, MockOptimizer)
    assert isinstance(scheduler.storage, SqlStorage)
    assert isinstance(scheduler.root_environment, MockEnv)
