#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Test fixtures for mlos_bench storage.
"""

import pytest

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql.storage import SqlStorage


@pytest.fixture
def exp_storage_memory_sql(tunable_groups: TunableGroups) -> Storage.Experiment:
    """
    Test fixture for in-memory SQLite3 storage.
    """
    storage = SqlStorage(
        tunables=tunable_groups,
        service=None,
        config={
            "drivername": "sqlite",
            "database": ":memory:",
        }
    )
    # pylint: disable=unnecessary-dunder-call
    return storage.experiment(
        experiment_id="Test-001",
        trial_id=1,
        root_env_config="environment.jsonc",
        description="pytest experiment",
        opt_target="score",
        opt_direction="min",
    ).__enter__()
