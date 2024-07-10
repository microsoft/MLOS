#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Configuration test fixtures for azure_vm_services in mlos_bench."""

from unittest.mock import patch

import pytest

from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.remote.azure import (
    AzureAuthService,
    AzureFileShareService,
    AzureNetworkService,
    AzureVMService,
)

# pylint: disable=redefined-outer-name


@pytest.fixture
def config_persistence_service() -> ConfigPersistenceService:
    """Test fixture for ConfigPersistenceService."""
    return ConfigPersistenceService()


@pytest.fixture
def azure_auth_service(
    config_persistence_service: ConfigPersistenceService,
    monkeypatch: pytest.MonkeyPatch,
) -> AzureAuthService:
    """Creates a dummy AzureAuthService for tests that require it."""
    auth = AzureAuthService(config={}, global_config={}, parent=config_persistence_service)
    monkeypatch.setattr(auth, "get_access_token", lambda: "TEST_TOKEN")
    return auth


@pytest.fixture
def azure_network_service(azure_auth_service: AzureAuthService) -> AzureNetworkService:
    """Creates a dummy Azure VM service for tests that require it."""
    return AzureNetworkService(
        config={
            "deploymentTemplatePath": (
                "services/remote/azure/arm-templates/azuredeploy-ubuntu-vm.jsonc"
            ),
            "subscription": "TEST_SUB",
            "resourceGroup": "TEST_RG",
            "deploymentTemplateParameters": {
                "location": "westus2",
            },
            "pollInterval": 1,
            "pollTimeout": 2,
        },
        global_config={
            "deploymentName": "TEST_DEPLOYMENT-VNET",
            "vnetName": "test-vnet",  # Should come from the upper-level config
        },
        parent=azure_auth_service,
    )


@pytest.fixture
def azure_vm_service(azure_auth_service: AzureAuthService) -> AzureVMService:
    """Creates a dummy Azure VM service for tests that require it."""
    return AzureVMService(
        config={
            "deploymentTemplatePath": (
                "services/remote/azure/arm-templates/azuredeploy-ubuntu-vm.jsonc"
            ),
            "subscription": "TEST_SUB",
            "resourceGroup": "TEST_RG",
            "deploymentTemplateParameters": {
                "location": "westus2",
            },
            "pollInterval": 1,
            "pollTimeout": 2,
        },
        global_config={
            "deploymentName": "TEST_DEPLOYMENT-VM",
            "vmName": "test-vm",  # Should come from the upper-level config
        },
        parent=azure_auth_service,
    )


@pytest.fixture
def azure_vm_service_remote_exec_only(azure_auth_service: AzureAuthService) -> AzureVMService:
    """Creates a dummy Azure VM service with no deployment template."""
    return AzureVMService(
        config={
            "subscription": "TEST_SUB",
            "resourceGroup": "TEST_RG",
            "pollInterval": 1,
            "pollTimeout": 2,
        },
        global_config={
            "vmName": "test-vm",  # Should come from the upper-level config
        },
        parent=azure_auth_service,
    )


@pytest.fixture
def azure_fileshare(config_persistence_service: ConfigPersistenceService) -> AzureFileShareService:
    """Creates a dummy AzureFileShareService for tests that require it."""
    with patch("mlos_bench.services.remote.azure.azure_fileshare.ShareClient"):
        return AzureFileShareService(
            config={
                "storageAccountName": "TEST_ACCOUNT_NAME",
                "storageFileShareName": "TEST_FS_NAME",
                "storageAccountKey": "TEST_ACCOUNT_KEY",
            },
            global_config={},
            parent=config_persistence_service,
        )
