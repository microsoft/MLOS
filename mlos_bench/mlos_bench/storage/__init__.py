#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Interfaces to the storage backends for OS Autotune.
"""

from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.storage_factory import from_config

__all__ = [
    'Storage',
    'from_config'
]
