#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Export test fixtures for mlos_bench storage."""

import mlos_bench.tests.storage.sql.fixtures as sql_storage_fixtures

# NOTE: For future storage implementation additions, we can refactor this to use
# lazy_fixture and parameterize the tests across fixtures but keep the test code the
# same.

# Expose some of those as local names so they can be picked up as fixtures by pytest.
storage = sql_storage_fixtures.storage
exp_storage = sql_storage_fixtures.exp_storage
exp_no_tunables_storage = sql_storage_fixtures.exp_no_tunables_storage
mixed_numerics_exp_storage = sql_storage_fixtures.mixed_numerics_exp_storage
exp_storage_with_trials = sql_storage_fixtures.exp_storage_with_trials
exp_no_tunables_storage_with_trials = sql_storage_fixtures.exp_no_tunables_storage_with_trials
mixed_numerics_exp_storage_with_trials = (
    sql_storage_fixtures.mixed_numerics_exp_storage_with_trials
)
exp_data = sql_storage_fixtures.exp_data
exp_no_tunables_data = sql_storage_fixtures.exp_no_tunables_data
mixed_numerics_exp_data = sql_storage_fixtures.mixed_numerics_exp_data
