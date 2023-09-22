#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.remote.ssh.ssh_host_service
"""

from subprocess import run

from mlos_bench.environments.status import Status

from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService
from mlos_bench.services.remote.ssh.ssh_service import SshClient

from mlos_bench.tests import requires_docker, check_socket, resolve_host_name
from mlos_bench.tests.services.remote.ssh import SshTestServerInfo, ALT_TEST_SERVER_NAME, SSH_TEST_SERVER_NAME


@requires_docker
def test_ssh_service_remote_exec(ssh_test_server: SshTestServerInfo, ssh_host_service: SshHostService) -> None:
    """Test the SshHostService remote_exec."""
    config = ssh_test_server.to_ssh_service_config()
    (status, results_info) = ssh_host_service.remote_exec(
        script=["hostname"],
        config=config,
        env_params={
            # TODO
        },
    )
    assert status == Status.PENDING
    assert "asyncRemoteExecResultsFuture" in results_info
    status, results = ssh_host_service.get_remote_exec_results(results_info)

    # Check that the SSH client was cached.
    connection_id = SshClient.id_from_params(ssh_test_server.to_connect_params())

    # pylint: disable=protected-access
    assert ssh_host_service._event_loop_thread_ssh_client_cache is not None
    connection, client = ssh_host_service._event_loop_thread_ssh_client_cache._cache[connection_id]
    assert connection is not None
    assert connection._username == ssh_test_server.username
    assert connection._host == ssh_test_server.hostname
    assert connection._port == ssh_test_server.port
    assert client is not None
    assert client._conn_event.is_set()

    assert status == Status.SUCCEEDED
    assert results["stdout"].strip() == SSH_TEST_SERVER_NAME
