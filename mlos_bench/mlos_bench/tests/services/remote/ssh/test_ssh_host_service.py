#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.remote.ssh.ssh_host_service
"""

import time

from mlos_bench.environments.status import Status

from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService
from mlos_bench.services.remote.ssh.ssh_service import SshClient

from mlos_bench.tests import requires_docker
from mlos_bench.tests.services.remote.ssh import SshTestServerInfo, ALT_TEST_SERVER_NAME, SSH_TEST_SERVER_NAME


@requires_docker
def test_ssh_service_remote_exec(ssh_test_server: SshTestServerInfo,
                                 alt_test_server: SshTestServerInfo,
                                 ssh_host_service: SshHostService) -> None:
    """
    Test the SshHostService remote_exec.

    This checks state of the service across multiple invocations and states to
    check for internal cache handling logic as well.
    """
    # pylint: disable=protected-access

    config = ssh_test_server.to_ssh_service_config()

    # Check that the SSH client isn't cached yet.
    connection_id = SshClient.id_from_params(ssh_test_server.to_connect_params())
    assert ssh_host_service._event_loop_thread_ssh_client_cache is not None
    connection_client = ssh_host_service._event_loop_thread_ssh_client_cache._cache.get(connection_id)
    assert connection_client is None

    (status, results_info) = ssh_host_service.remote_exec(
        script=["hostname"],
        config=config,
        env_params={},
    )
    assert status == Status.PENDING
    assert "asyncRemoteExecResultsFuture" in results_info
    status, results = ssh_host_service.get_remote_exec_results(results_info)
    assert status == Status.SUCCEEDED
    assert results["stdout"].strip() == SSH_TEST_SERVER_NAME

    # Check that the client caching is behaving as expected.
    connection, client = ssh_host_service._event_loop_thread_ssh_client_cache._cache[connection_id]
    assert connection is not None
    assert connection._username == ssh_test_server.username
    assert connection._host == ssh_test_server.hostname
    assert connection._port == ssh_test_server.port
    local_port = connection._local_port
    assert local_port
    assert client is not None
    assert client._conn_event.is_set()

    # Connect to a different server.
    (status, results_info) = ssh_host_service.remote_exec(
        script=["hostname"],
        config=alt_test_server.to_ssh_service_config(),
        env_params={},
    )
    assert status == Status.PENDING
    assert "asyncRemoteExecResultsFuture" in results_info
    status, results = ssh_host_service.get_remote_exec_results(results_info)
    assert status == Status.SUCCEEDED
    assert results["stdout"].strip() == ALT_TEST_SERVER_NAME

    # Test reusing the existing connection.
    (status, results_info) = ssh_host_service.remote_exec(
        script=["echo BAR=$BAR && false"],
        config=config,
        # Also test interacting with environment_variables.
        env_params={
            "BAR": "bar",   # unused, making sure it doesn't carry over with cached connections
        },
    )
    status, results = ssh_host_service.get_remote_exec_results(results_info)
    assert status == Status.FAILED
    assert results["stdout"].strip() == "BAR=bar"
    connection, client = ssh_host_service._event_loop_thread_ssh_client_cache._cache[connection_id]
    assert connection._local_port == local_port

    # Close the connection (gracefully)
    connection.close()

    # Try and reconnect and see if it detects the closed connection and starts over.
    (status, results_info) = ssh_host_service.remote_exec(
        script=[
            # Test multi-string scripts.
            "echo FOO=$FOO\n",
            # Test multi-line strings.
            "echo BAR=$BAR\necho BAZ=$BAZ",
        ],
        config=config,
        # Also test interacting with environment_variables.
        env_params={
            'FOO': 'foo',
        },
    )
    status, results = ssh_host_service.get_remote_exec_results(results_info)
    assert status == Status.SUCCEEDED
    stdout = str(results["stdout"])
    lines = stdout.splitlines()
    assert lines == [
        "FOO=foo",
        "BAR=",
        "BAZ=",
    ]
    # Make sure it looks like we reconnected.
    connection, client = ssh_host_service._event_loop_thread_ssh_client_cache._cache[connection_id]
    assert connection._local_port != local_port


# TODO: Test rebooting (changes the port number unfortunately).
