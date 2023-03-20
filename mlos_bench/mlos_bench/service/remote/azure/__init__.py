#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Azure-specific benchmark environments for mlos_bench.
"""

from mlos_bench.service.remote.azure.azure_services import AzureVMService
from mlos_bench.service.remote.azure.azure_fileshare import AzureFileShareService


__all__ = [
    'AzureVMService',
    'AzureFileShareService',
]
