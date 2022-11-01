"""
Configuration test fixtures for azure_services in mlos_bench.
"""

from unittest.mock import patch
import pytest

from mlos_bench.environment.azure.azure_services import AzureVMService
from mlos_bench.environment.azure.azure_fileshare import AzureFileShareService


@pytest.fixture
def azure_vm_service():
    """
    Creates a dummy Azure VM service for tests that require it.
    """
    service = AzureVMService(config={
        "config_dir": "./mlos_bench/config",
        "deployTemplatePath": "azure/arm-templates/azuredeploy-ubuntu-vm.json",
        "deploymentName": "TEST_DEPLOYMENT",
        "subscription": "TEST_SUB",
        "resourceGroup": "TEST_RG",
        "accessToken": "TEST_TOKEN",
        "vmName": "dummy-vm",
        "pollInterval": 1,
        "pollTimeout": 2
    })

    return service


@pytest.fixture
def azure_fileshare():
    """
    Creates a dummy AzureFileShareService for tests that require it.
    """
    with patch("mlos_bench.environment.azure.azure_fileshare.ShareClient"):
        fileshare = AzureFileShareService(config={
            "storageAccountName": "TEST_ACCOUNT_NAME",
            "storageFileShareName": "TEST_FS_NAME",
            "storageAccountKey": "TEST_ACCOUNT_KEY",
            "mountPoint": "/test/mnt/point",
        })
        return fileshare
