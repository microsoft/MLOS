"""
Azure-specific benchmark environments for OS Autotune.
"""

from mlos_bench.environment.azure.azure_vm import VMEnv
from mlos_bench.environment.azure.azure_os import OSEnv
from mlos_bench.environment.azure.azure_services import AzureVMService


__all__ = [
    'VMEnv',
    'OSEnv',
    'AzureVMService'
]
