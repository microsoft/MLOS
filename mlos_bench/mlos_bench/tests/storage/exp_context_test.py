#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for the storage subsystem."""

from mlos_bench.storage.base_storage import Storage


def test_exp_context(exp_storage: Storage.Experiment) -> None:
    """Try to retrieve old experimental data from the empty storage."""
    # pylint: disable=protected-access
    assert exp_storage._in_context
