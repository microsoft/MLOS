#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for the storage subsystem.
"""

from mlos_bench.storage import Storage

# pylint: disable=redefined-outer-name


def test_exp_create(exp_storage_memory_sql: Storage.Experiment):
    """
    Try to create a new experiment in storage.
    """
    assert exp_storage_memory_sql is not None
