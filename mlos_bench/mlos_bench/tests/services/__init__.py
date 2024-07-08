#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.

Used to make mypy happy about multiple conftest.py modules.
"""

from .local import MockLocalExecService
from .remote import MockFileShareService, MockRemoteExecService, MockVMService

__all__ = [
    "MockLocalExecService",
    "MockFileShareService",
    "MockRemoteExecService",
    "MockVMService",
]
