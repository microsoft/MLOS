#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Export test fixtures for mlos_bench storage.
"""

import mlos_bench.tests.storage.fixtures as storage_fixtures

# Expose some of those as local names so they can be picked up as fixtures by pytest.
storage_memory_sql = storage_fixtures.storage_memory_sql
exp_storage_memory_sql = storage_fixtures.exp_storage_memory_sql
exp_storage_memory_sql_with_trials = storage_fixtures.exp_storage_memory_sql_with_trials
exp_data = storage_fixtures.exp_data
