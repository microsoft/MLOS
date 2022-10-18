"""
Configuration test fixtures for azure_services in mlos_bench.
"""

import pytest

from mlos_bench.environment.azure.azure_services import AzureVMService


@pytest.fixture
def azure_vm_service():
    """
    Creates a dummy Azure VM service for tests that require it.
    """
    service = AzureVMService(config={
        "deployTemplatePath": "./mlos_bench/config/azure/arm-templates/azuredeploy-ubuntu-vm.json",
        "deploymentName": "TEST_DEPLOYMENT",
        "subscription": "TEST_SUB",
        "resourceGroup": "TEST_RG",
        "accessToken": "TEST_TOKEN",
        "vmName": "dummy-vm",
        "pollInterval": 1,
        "pollTimeout": 2
    })

    return service
