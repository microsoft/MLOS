#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for mlos_bench.services.remote.azure.azure_network_services."""

from unittest.mock import MagicMock, patch

import pytest
import requests.exceptions as requests_ex

from mlos_bench.environments.status import Status
from mlos_bench.services.remote.azure.azure_auth import AzureAuthService
from mlos_bench.services.remote.azure.azure_network_services import AzureNetworkService
from mlos_bench.tests.services.remote.azure import make_httplib_json_response


@pytest.mark.parametrize(
    ("total_retries", "operation_status"),
    [
        (2, Status.SUCCEEDED),
        (1, Status.FAILED),
        (0, Status.FAILED),
    ],
)
@patch("urllib3.connectionpool.HTTPConnectionPool._get_conn")
def test_wait_network_deployment_retry(
    mock_getconn: MagicMock,
    total_retries: int,
    operation_status: Status,
    azure_network_service: AzureNetworkService,
) -> None:
    """Test retries of the network deployment operation."""
    # Simulate intermittent connection issues with multiple connection errors
    # Sufficient retry attempts should result in success, otherwise a graceful failure state
    mock_getconn.return_value.getresponse.side_effect = [
        make_httplib_json_response(200, {"properties": {"provisioningState": "Running"}}),
        requests_ex.ConnectionError(
            "Connection aborted", OSError(107, "Transport endpoint is not connected")
        ),
        requests_ex.ConnectionError(
            "Connection aborted", OSError(107, "Transport endpoint is not connected")
        ),
        make_httplib_json_response(200, {"properties": {"provisioningState": "Running"}}),
        make_httplib_json_response(200, {"properties": {"provisioningState": "Succeeded"}}),
    ]

    (status, _) = azure_network_service.wait_network_deployment(
        params={
            "pollInterval": 0.1,
            "requestTotalRetries": total_retries,
            "deploymentName": "TEST_DEPLOYMENT1",
            "subscription": "TEST_SUB1",
            "resourceGroup": "TEST_RG1",
        },
        is_setup=True,
    )
    assert status == operation_status


@pytest.mark.parametrize(
    ("operation_name", "accepts_params"),
    [
        ("deprovision_network", True),
    ],
)
@pytest.mark.parametrize(
    ("http_status_code", "operation_status"),
    [
        (200, Status.SUCCEEDED),
        (202, Status.PENDING),
        # These should succeed since we set ignore_errors=True by default
        (401, Status.SUCCEEDED),
        (404, Status.SUCCEEDED),
    ],
)
@patch("mlos_bench.services.remote.azure.azure_deployment_services.requests")
# pylint: disable=too-many-arguments
def test_network_operation_status(
    mock_requests: MagicMock,
    azure_network_service: AzureNetworkService,
    operation_name: str,
    accepts_params: bool,
    http_status_code: int,
    operation_status: Status,
) -> None:
    """Test network operation status."""
    mock_response = MagicMock()
    mock_response.status_code = http_status_code
    mock_requests.post.return_value = mock_response

    operation = getattr(azure_network_service, operation_name)
    with pytest.raises(ValueError):
        # Missing vnetName should raise ValueError
        (status, _) = operation({}) if accepts_params else operation()
    (status, _) = operation({"vnetName": "test-vnet"}) if accepts_params else operation()
    assert status == operation_status


@pytest.fixture
def test_azure_network_service_no_deployment_template(
    azure_auth_service: AzureAuthService,
) -> None:
    """Tests creating a network services without a deployment template (should fail)."""
    with pytest.raises(ValueError):
        _ = AzureNetworkService(
            config={
                "deploymentTemplatePath": None,
                "deploymentTemplateParameters": {
                    "location": "westus2",
                },
            },
            parent=azure_auth_service,
        )

    with pytest.raises(ValueError):
        _ = AzureNetworkService(
            config={
                # "deploymentTemplatePath": None,
                "deploymentTemplateParameters": {
                    "location": "westus2",
                },
            },
            parent=azure_auth_service,
        )
