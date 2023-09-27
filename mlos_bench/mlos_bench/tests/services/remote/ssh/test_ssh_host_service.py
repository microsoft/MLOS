#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.remote.ssh.ssh_host_service
"""

import time

from logging import warning

import pytest
from pytest_docker.plugin import Services as DockerServices

from mlos_bench.environments.status import Status

from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService
from mlos_bench.services.remote.ssh.ssh_service import SshClient

from mlos_bench.tests import requires_docker
from mlos_bench.tests.services.remote.ssh import (SshTestServerInfo,
                                                  ALT_TEST_SERVER_NAME,
                                                  SSH_TEST_SERVER_NAME,
                                                  wait_docker_service_socket)


@requires_docker
@pytest.mark.xdist_group("ssh_test_server")
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
    assert connection._port == ssh_test_server.get_port()
    local_port = connection._local_port
    assert local_port
    assert client is not None
    assert client._conn_event.is_set()

    # Connect to a different server.
    (status, results_info) = ssh_host_service.remote_exec(
        script=["hostname"],
        config=alt_test_server.to_ssh_service_config(),
        env_params={
            "UNUSED": "unused",  # unused, making sure it doesn't carry over with cached connections
        },
    )
    assert status == Status.PENDING
    assert "asyncRemoteExecResultsFuture" in results_info
    status, results = ssh_host_service.get_remote_exec_results(results_info)
    assert status == Status.SUCCEEDED
    assert results["stdout"].strip() == ALT_TEST_SERVER_NAME

    # Test reusing the existing connection.
    (status, results_info) = ssh_host_service.remote_exec(
        script=["echo BAR=$BAR && echo UNUSED=$UNUSED && false"],
        config=config,
        # Also test interacting with environment_variables.
        env_params={
            "BAR": "bar",
        },
    )
    status, results = ssh_host_service.get_remote_exec_results(results_info)
    assert status == Status.FAILED  # should retain exit code from "false"
    stdout = str(results["stdout"])
    assert stdout.splitlines() == [
        "BAR=bar",
        "UNUSED=",
    ]
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


@requires_docker
@pytest.mark.parametrize("graceful", [True, False])
@pytest.mark.xdist_group("ssh_test_server")
def test_ssh_service_reboot(docker_services: DockerServices,
                            alt_test_server: SshTestServerInfo,
                            ssh_host_service: SshHostService,
                            graceful: bool) -> None:
    """
    Test the SshHostService reboot.
    """
    # pylint: disable=protected-access

    # Note: rebooting changes the port number unfortunately, but makes it
    # easier to check for success.
    # Also, it may cause issues with other parallel unit tests, so we run it as
    # a part of the same unit test for now.
    alt_test_server_ssh_service_config = alt_test_server.to_ssh_service_config()
    (status, results_info) = ssh_host_service.remote_exec(
        script=[
            "echo \"sleeping...\"",
            "sleep 30",
            "echo \"shouldn't reach this point\""
        ],
        config=alt_test_server_ssh_service_config,
        env_params={},
    )
    assert status == Status.PENDING
    # Wait a moment for that to start in the background thread.
    time.sleep(0.5)

    # Now try to restart the server (gracefully).
    # TODO: Test graceful vs. forceful.
    if graceful:
        (status, reboot_results_info) = ssh_host_service.reboot(params=alt_test_server_ssh_service_config)
        assert status == Status.PENDING

        (status, reboot_results_info) = ssh_host_service.wait_os_operation(reboot_results_info)
        # NOTE: reboot/shutdown ops mostly return FAILED, even though the reboot succeeds.
        print(f"reboot status: {status} {reboot_results_info}")
    else:
        (status, kill_results_info) = ssh_host_service.remote_exec(
            script=["kill -9 1; kill -9 -1"],
            config=alt_test_server_ssh_service_config,
            env_params={},
        )
        (status, kill_results_info) = ssh_host_service.get_remote_exec_results(kill_results_info)
        print(f"kill status: {status} {kill_results_info}")

    # TODO: Check for decent error handling on disconnects.
    status, results = ssh_host_service.get_remote_exec_results(results_info)
    assert status == Status.FAILED
    stdout = str(results["stdout"])
    assert "sleeping" in stdout
    assert "shouldn't reach this point" not in stdout

    # Give docker some time to restart the service after the "reboot".
    # Note: this relies on having `restart: always` in the docker-compose.yml file.
    time.sleep(1)

    # try to reconnect and see if the port changed
    alt_test_server_ssh_service_config_new = alt_test_server.to_ssh_service_config(uncached=True)
    assert alt_test_server_ssh_service_config_new["ssh_port"] != alt_test_server_ssh_service_config["ssh_port"]

    wait_docker_service_socket(docker_services, alt_test_server.hostname, alt_test_server_ssh_service_config_new["ssh_port"])

    (status, results_info) = ssh_host_service.remote_exec(
        script=["hostname"],
        config=alt_test_server_ssh_service_config_new,
        env_params={},
    )
    status, results = ssh_host_service.get_remote_exec_results(results_info)
    assert status == Status.SUCCEEDED
    assert results["stdout"].strip() == ALT_TEST_SERVER_NAME
