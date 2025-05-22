#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for :py:class:`mlos_bench.schedulers` and their internals.
"""

import pytest
import unittest.mock

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
