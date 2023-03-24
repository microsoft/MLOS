#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Interfaces to the storage backends for OS Autotune.
"""

from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.sql_storage import SqlStorage

__all__ = [
    'Storage',
    'SqlStorage',
]
