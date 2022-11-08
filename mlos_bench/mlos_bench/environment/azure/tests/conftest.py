"""
Configuration test fixtures for azure_services in mlos_bench.
"""

from unittest.mock import patch
import pytest

from mlos_bench.environment import ConfigPersistenceService
from mlos_bench.environment.azure import AzureVMService, AzureFileShareService

# pylint: disable=redefined-outer-name


@pytest.fixture
def config_persistence_service():
    """
    Test fixture for ConfigPersistenceService.
    """
    return ConfigPersistenceService({
        "config_path": [
            "./mlos_bench/config"
        ]
    })


@pytest.fixture
def azure_vm_service(config_persistence_service):
    """
    Creates a dummy Azure VM service for tests that require it.
    """
    return AzureVMService(config={
        "deployTemplatePath": "azure/arm-templates/azuredeploy-ubuntu-vm.json",
        "deploymentName": "TEST_DEPLOYMENT",
        "subscription": "TEST_SUB",
        "resourceGroup": "TEST_RG",
        "accessToken": "TEST_TOKEN",
        "vmName": "dummy-vm",
        "pollInterval": 1,
        "pollTimeout": 2
    }, parent=config_persistence_service)


@pytest.fixture
def azure_fileshare():
    """
    Creates a dummy AzureFileShareService for tests that require it.
    """
    with patch("mlos_bench.environment.azure.azure_fileshare.ShareClient"):
        return AzureFileShareService(config={
            "storageAccountName": "TEST_ACCOUNT_NAME",
            "storageFileShareName": "TEST_FS_NAME",
            "storageAccountKey": "TEST_ACCOUNT_KEY"
        }, parent=config_persistence_service)
