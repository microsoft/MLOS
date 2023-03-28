#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for the storage subsystem.
"""

from mlos_bench.storage import Storage

# pylint: disable=redefined-outer-name


def test_exp_load_empty(exp_storage_memory_sql: Storage.Experiment):
    """
    Try to retrieve old experimental data from the empty storage.
    """
    (configs, scores) = exp_storage_memory_sql.load('score')
    assert configs is None
    assert scores is None

