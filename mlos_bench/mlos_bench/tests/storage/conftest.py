#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Export test fixtures for mlos_bench storage.
"""

from mlos_bench.tests.storage import (
    storage_memory_sql as storage_memory_sql_fixture,
    exp_storage_memory_sql as exp_storage_memory_sql_fixture,
    exp_storage_memory_sql_with_trials as exp_storage_memory_sql_with_trials_fixture,
    exp_data as exp_data_fixture,
)

storage_memory_sql = storage_memory_sql_fixture
exp_storage_memory_sql = exp_storage_memory_sql_fixture
exp_storage_memory_sql_with_trials = exp_storage_memory_sql_with_trials_fixture
exp_data = exp_data_fixture
