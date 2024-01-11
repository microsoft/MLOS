#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for loading the experiment metadata.
"""

from mlos_bench.storage.base_storage import Storage


def test_load_empty_exp_data(storage_memory_sql: Storage, exp_storage_memory_sql: Storage.Experiment) -> None:
    """
    Try to retrieve old experimental data from the empty storage.
    """
    exp = storage_memory_sql.experiments[exp_storage_memory_sql.experiment_id]
    assert exp.exp_id == exp_storage_memory_sql.experiment_id
    assert exp.description == exp_storage_memory_sql.description
    # Only support single objective for now.
    assert exp.objectives == {exp_storage_memory_sql.opt_target: exp_storage_memory_sql.opt_direction}
