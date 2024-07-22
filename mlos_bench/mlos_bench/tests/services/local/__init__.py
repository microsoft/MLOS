#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.local.

Used to make mypy happy about multiple conftest.py modules.
"""

from .mock import MockLocalExecService

__all__ = [
    "MockLocalExecService",
]
