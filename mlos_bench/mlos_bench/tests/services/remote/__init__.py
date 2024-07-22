#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.remote.

Used to make mypy happy about multiple conftest.py modules.
"""

from .mock.mock_fileshare_service import MockFileShareService
from .mock.mock_remote_exec_service import MockRemoteExecService
from .mock.mock_vm_service import MockVMService

__all__ = [
    "MockFileShareService",
    "MockRemoteExecService",
    "MockVMService",
]
