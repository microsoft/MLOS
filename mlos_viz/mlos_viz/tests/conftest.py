#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Export test fixtures for mlos_viz.
"""

from mlos_bench.tests.tunable_groups import (
    tunable_groups_config as tunable_groups_config_fixture,
    tunable_groups as tunable_groups_fixture,
)
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

tunable_groups_config = tunable_groups_config_fixture
tunable_groups = tunable_groups_fixture

# TODO: Validate the non-display via rcParams tweaks at upper levels works on Windows too.
