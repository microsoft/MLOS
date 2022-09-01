"""
Tests for mlos_bench.environment.azure.azure_services
"""

from unittest.mock import MagicMock, patch

import pytest

from mlos_bench.environment import Status

# pylint: disable=missing-function-docstring
# pylint: disable=too-many-arguments

@pytest.mark.parametrize(
    ("operation_name", "accepts_params"), [
        ("vm_start", True),
        ("vm_stop", False),
        ("vm_deprovision", False),
        ("vm_reboot", False),
    ])
@pytest.mark.parametrize(
    ("http_status_code", "operation_status"), [
        (200, Status.READY),
        (202, Status.PENDING),
        (401, Status.FAILED),
        (404, Status.FAILED),
    ])
@patch("mlos_bench.environment.azure.azure_services.requests")
def test_vm_operation_status(mock_requests, azure_vm_service, operation_name, accepts_params, http_status_code, operation_status):
    mock_response = MagicMock()
    mock_response.status_code = http_status_code
    mock_requests.post.return_value = mock_response

    operation = getattr(azure_vm_service, operation_name)
    if accepts_params:
        status, _ = operation({})
    else:
        status, _ = operation()

    assert status == operation_status


@patch("mlos_bench.environment.azure.azure_services.time.sleep")
@patch("mlos_bench.environment.azure.azure_services.requests")
def test_wait_vm_operation_ready(mock_requests, mock_sleep, azure_vm_service):

    # Mock response header
    async_url = "DUMMY_ASYNC_URL"
    retry_after = 12345
    params = {
        "asyncResultsUrl": async_url,
        "pollPeriod": retry_after,
    }

    mock_status_response = MagicMock(status_code=200)
    mock_status_response.json.return_value = {
        "status": "Succeeded",
    }
    mock_requests.get.return_value = mock_status_response

    status, _ = azure_vm_service.wait_vm_operation(params)

    assert (async_url, ) == mock_requests.get.call_args[0]
    assert (retry_after, ) == mock_sleep.call_args[0]
    assert status == Status.READY


@patch("mlos_bench.environment.azure.azure_services.time.sleep")
@patch("mlos_bench.environment.azure.azure_services.requests")
def test_wait_vm_operation_timeout(mock_requests, mock_sleep, azure_vm_service):

    # Mock response header
    async_url = "DUMMY_ASYNC_URL"
    retry_after = 10
    params = {
        "asyncResultsUrl": async_url,
        "pollPeriod": retry_after,
    }

    mock_status_response = MagicMock(status_code=200)
    mock_status_response.json.return_value = {
        "status": "InProgress",
    }
    mock_requests.get.return_value = mock_status_response

    with pytest.raises(TimeoutError):
        azure_vm_service.wait_vm_operation(params, timeout=100)

    assert (async_url, ) == mock_requests.get.call_args[0]
    assert mock_sleep.call_count == 10
    assert mock_requests.get.call_count == 10
