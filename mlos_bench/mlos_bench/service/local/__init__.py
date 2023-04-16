#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Local scheduler side Services for mlos_bench.
"""

from mlos_bench.service.types.local_exec_type import SupportsLocalExec
from mlos_bench.service.local.local_exec import LocalExecService


__all__ = [
    'SupportsLocalExec',
    'LocalExecService',
]
