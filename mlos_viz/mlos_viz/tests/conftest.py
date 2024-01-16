#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Export test fixtures for mlos_viz.
"""

from mlos_bench.tests.storage import (
    storage_memory_sql as storage_memory_sql_fixture,
    exp_storage_memory_sql as exp_storage_memory_sql_fixture,
)

exp_storage_memory_sql = exp_storage_memory_sql_fixture
storage_memory_sql = storage_memory_sql_fixture
