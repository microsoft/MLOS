#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Service types for implementing declaring Service behavior for Environments to use in mlos_bench.
"""

from mlos_bench.service.types.config_loader_type import SupportsConfigLoading
from mlos_bench.service.types.fileshare_type import SupportsFileShareOps
from mlos_bench.service.types.host_provisioner_type import SupportsHostProvisioning
from mlos_bench.service.types.host_ops_type import SupportsHostOps
from mlos_bench.service.types.os_ops_type import SupportsOSOps
from mlos_bench.service.types.local_exec_type import SupportsLocalExec
from mlos_bench.service.types.remote_exec_type import SupportsRemoteExec


__all__ = [
    'SupportsConfigLoading',
    'SupportsFileShareOps',
    'SupportsHostOps',
    'SupportsHostProvisioning',
    'SupportsLocalExec',
    'SupportsOSOps',
    'SupportsRemoteExec',
]
