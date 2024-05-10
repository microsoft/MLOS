#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Azure-specific benchmark environments for mlos_bench.
"""

from mlos_bench.services.remote.azure.azure_auth import AzureAuthService
from mlos_bench.services.remote.azure.azure_fileshare import AzureFileShareService
from mlos_bench.services.remote.azure.azure_network_services import AzureNetworkService
from mlos_bench.services.remote.azure.azure_saas import AzureSaaSConfigService
from mlos_bench.services.remote.azure.azure_vm_services import AzureVMService


__all__ = [
    'AzureAuthService',
    'AzureFileShareService',
    'AzureNetworkService',
    'AzureSaaSConfigService',
    'AzureVMService',
]
