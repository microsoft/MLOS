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
        (200, Status.SUCCEEDED),
        (202, Status.PENDING),
        (401, Status.FAILED),
        (404, Status.FAILED),
    ])
@patch("mlos_bench.environment.azure.azure_services.requests")
def test_vm_operation_status(mock_requests, azure_vm_service, operation_name,
                             accepts_params, http_status_code, operation_status):

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
        "pollInterval": retry_after,
    }

    mock_status_response = MagicMock(status_code=200)
    mock_status_response.json.return_value = {
        "status": "Succeeded",
    }
    mock_requests.get.return_value = mock_status_response

    status, _ = azure_vm_service.wait_vm_operation(params)

    assert (async_url, ) == mock_requests.get.call_args[0]
    assert (retry_after, ) == mock_sleep.call_args[0]
    assert status.is_succeeded


@patch("mlos_bench.environment.azure.azure_services.requests")
def test_wait_vm_operation_timeout(mock_requests, azure_vm_service):

    # Mock response header
    params = {
        "asyncResultsUrl": "DUMMY_ASYNC_URL",
        "pollInterval": 1
    }

    mock_status_response = MagicMock(status_code=200)
    mock_status_response.json.return_value = {
        "status": "InProgress",
    }
    mock_requests.get.return_value = mock_status_response

    (status, _) = azure_vm_service.wait_vm_operation(params)
    assert status == Status.TIMED_OUT


@pytest.mark.parametrize(
    ("http_status_code", "operation_status"), [
        (200, Status.SUCCEEDED),
        (202, Status.PENDING),
        (401, Status.FAILED),
        (404, Status.FAILED),
    ])
@patch("mlos_bench.environment.azure.azure_services.requests")
def test_remote_exec_status(mock_requests, azure_vm_service, http_status_code, operation_status):

    script = ["command_1", "command_2"]

    mock_response = MagicMock()
    mock_response.status_code = http_status_code
    mock_requests.post.return_value = mock_response

    status, _ = azure_vm_service.remote_exec(script, {})

    assert status == operation_status


@patch("mlos_bench.environment.azure.azure_services.requests")
def test_remote_exec_headers_output(mock_requests, azure_vm_service):

    async_url_key = "asyncResultsUrl"
    async_url_value = "DUMMY_ASYNC_URL"
    script = ["command_1", "command_2"]

    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_response.headers = {
        "Azure-AsyncOperation": async_url_value
    }
    mock_requests.post.return_value = mock_response

    _, cmd_output = azure_vm_service.remote_exec(script, {
        "param_1": 123,
        "param_2": "abc",
    })

    assert async_url_key in cmd_output
    assert cmd_output[async_url_key] == async_url_value

    assert mock_requests.post.call_args[1]["json"] == {
        "commandId": "RunShellScript",
        "script": script,
        "parameters": [
            {"name": "param_1", "value": 123},
            {"name": "param_2", "value": "abc"}
        ]
    }


@pytest.mark.parametrize(
    ("operation_status", "wait_output", "results_output"), [
        (Status.SUCCEEDED, {
            "properties": {
                "output": [
                    {"message": "DUMMY_STDOUT_STDERR"},
                ]
            }
        }, [
            {"message": "DUMMY_STDOUT_STDERR"},
        ]),
        (Status.PENDING, {}, {}),
        (Status.FAILED, {}, {}),
    ])
def test_get_remote_exec_results(azure_vm_service, operation_status: Status,
                                 wait_output: dict, results_output: dict):

    params = {"asyncResultsUrl": "DUMMY_ASYNC_URL"}

    mock_wait_vm_operation = MagicMock()
    mock_wait_vm_operation.return_value = (operation_status, wait_output)
    azure_vm_service.wait_vm_operation = mock_wait_vm_operation

    status, cmd_output = azure_vm_service.get_remote_exec_results(params)

    assert status == operation_status
    assert mock_wait_vm_operation.call_args[0][0] == params
    assert cmd_output == results_output
