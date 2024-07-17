#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Export test fixtures for mlos_viz."""

from mlos_bench.tests import tunable_groups_fixtures
from mlos_bench.tests.storage.sql import fixtures as sql_storage_fixtures

# Expose some of those as local names so they can be picked up as fixtures by pytest.

storage = sql_storage_fixtures.storage
exp_storage = sql_storage_fixtures.exp_storage
exp_storage_with_trials = sql_storage_fixtures.exp_storage_with_trials
exp_data = sql_storage_fixtures.exp_data

tunable_groups_config = tunable_groups_fixtures.tunable_groups_config
tunable_groups = tunable_groups_fixtures.tunable_groups
