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
from mlos_bench.storage.sql_storage import SqlStorage


@pytest.fixture
def exp_storage_memory_sql(tunable_groups: TunableGroups) -> Storage.Experiment:
    """
    Test fixture for in-memory SQLite3 storage.
    """
    storage = SqlStorage(tunable_groups, {
        "experimentId": "pytest",
        "trialId": 1,
        "db_module": "sqlite3",
        "connect_args": {
            "database": ":memory:",
            "isolation_level": None
        },
        "init_script": "mlos_bench/db/db_schema_sqlite.sql"
    })
    # pylint: disable=unnecessary-dunder-call
    return storage.experiment().__enter__()
