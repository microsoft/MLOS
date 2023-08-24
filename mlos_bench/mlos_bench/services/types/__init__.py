#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Service types for implementing declaring Service behavior for Environments to use in mlos_bench.
"""

from mlos_bench.services.types.config_loader_type import SupportsConfigLoading
from mlos_bench.services.types.fileshare_type import SupportsFileShareOps
from mlos_bench.services.types.vm_provisioner_type import SupportsVMOps
from mlos_bench.services.types.local_exec_type import SupportsLocalExec
from mlos_bench.services.types.remote_exec_type import SupportsRemoteExec


__all__ = [
    'SupportsConfigLoading',
    'SupportsFileShareOps',
    'SupportsVMOps',
    'SupportsLocalExec',
    'SupportsRemoteExec',
]
