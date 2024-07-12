#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for mlos_bench.services.remote.ssh.ssh_host_service."""

import logging
import time
from subprocess import CalledProcessError, run

from pytest_docker.plugin import Services as DockerServices

from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService
from mlos_bench.services.remote.ssh.ssh_service import SshClient
from mlos_bench.tests import requires_docker
from mlos_bench.tests.services.remote.ssh import (
    ALT_TEST_SERVER_NAME,
    REBOOT_TEST_SERVER_NAME,
    SSH_TEST_SERVER_NAME,
    SshTestServerInfo,
    wait_docker_service_socket,
)

_LOG = logging.getLogger(__name__)


@requires_docker
def test_ssh_service_remote_exec(
    ssh_test_server: SshTestServerInfo,
    alt_test_server: SshTestServerInfo,
    ssh_host_service: SshHostService,
) -> None:
    """
    Test the SshHostService remote_exec.

    This checks state of the service across multiple invocations and states to check for
    internal cache handling logic as well.
    """
    # pylint: disable=protected-access
    with ssh_host_service:
        config = ssh_test_server.to_ssh_service_config()

        connection_id = SshClient.id_from_params(ssh_test_server.to_connect_params())
        assert ssh_host_service._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE is not None
        connection_client = ssh_host_service._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE._cache.get(
            connection_id
        )
        assert connection_client is None

        (status, results_info) = ssh_host_service.remote_exec(
            script=["hostname"],
            config=config,
            env_params={},
        )
        assert status.is_pending()
        assert "asyncRemoteExecResultsFuture" in results_info
        status, results = ssh_host_service.get_remote_exec_results(results_info)
        assert status.is_succeeded()
        assert results["stdout"].strip() == SSH_TEST_SERVER_NAME

        # Check that the client caching is behaving as expected.
        connection, client = ssh_host_service._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE._cache[
            connection_id
        ]
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
                # unused, making sure it doesn't carry over with cached connections
                "UNUSED": "unused",
            },
        )
        assert status.is_pending()
        assert "asyncRemoteExecResultsFuture" in results_info
        status, results = ssh_host_service.get_remote_exec_results(results_info)
        assert status.is_succeeded()
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
        assert status.is_failed()  # should retain exit code from "false"
        stdout = str(results["stdout"])
        assert stdout.splitlines() == [
            "BAR=bar",
            "UNUSED=",
        ]
        connection, client = ssh_host_service._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE._cache[
            connection_id
        ]
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
                "FOO": "foo",
            },
        )
        status, results = ssh_host_service.get_remote_exec_results(results_info)
        assert status.is_succeeded()
        stdout = str(results["stdout"])
        lines = stdout.splitlines()
        assert lines == [
            "FOO=foo",
            "BAR=",
            "BAZ=",
        ]
        # Make sure it looks like we reconnected.
        connection, client = ssh_host_service._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE._cache[
            connection_id
        ]
        assert connection._local_port != local_port

    # Make sure the cache is cleaned up on context exit.
    assert len(SshHostService._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE) == 0


def check_ssh_service_reboot(
    docker_services: DockerServices,
    reboot_test_server: SshTestServerInfo,
    ssh_host_service: SshHostService,
    graceful: bool,
) -> None:
    """Check the SshHostService reboot operation."""
    # Note: rebooting changes the port number unfortunately, but makes it
    # easier to check for success.
    # Also, it may cause issues with other parallel unit tests, so we run it as
    # a part of the same unit test for now.
    with ssh_host_service:
        reboot_test_srv_ssh_svc_conf = reboot_test_server.to_ssh_service_config(uncached=True)
        (status, results_info) = ssh_host_service.remote_exec(
            script=['echo "sleeping..."', "sleep 30", 'echo "should not reach this point"'],
            config=reboot_test_srv_ssh_svc_conf,
            env_params={},
        )
        assert status.is_pending()
        # Wait a moment for that to start in the background thread.
        time.sleep(1)

        # Now try to restart the server.
        (status, reboot_results_info) = ssh_host_service.reboot(
            params=reboot_test_srv_ssh_svc_conf,
            force=not graceful,
        )
        assert status.is_pending()

        (status, reboot_results_info) = ssh_host_service.wait_os_operation(reboot_results_info)
        # NOTE: reboot/shutdown ops mostly return FAILED, even though the reboot succeeds.
        _LOG.debug("reboot status: %s: %s", status, reboot_results_info)

        # Check for decent error handling on disconnects.
        status, results = ssh_host_service.get_remote_exec_results(results_info)
        assert status.is_failed()
        stdout = str(results["stdout"])
        assert "sleeping" in stdout
        assert "should not reach this point" not in stdout

        reboot_test_srv_ssh_svc_conf_new: dict = {}
        for _ in range(0, 3):
            # Give docker some time to restart the service after the "reboot".
            # Note: this relies on having a `restart_policy` in the docker-compose.yml file.
            time.sleep(1)
            # try to reconnect and see if the port changed
            try:
                run_res = run(
                    "docker ps | grep mlos_bench-test- | grep reboot",
                    shell=True,
                    capture_output=True,
                    check=False,
                )
                print(run_res.stdout.decode())
                print(run_res.stderr.decode())
                reboot_test_srv_ssh_svc_conf_new = reboot_test_server.to_ssh_service_config(
                    uncached=True
                )
                if (
                    reboot_test_srv_ssh_svc_conf_new["ssh_port"]
                    != reboot_test_srv_ssh_svc_conf["ssh_port"]
                ):
                    break
            except CalledProcessError as ex:
                _LOG.info("Failed to check port for reboot test server: %s", ex)
        assert (
            reboot_test_srv_ssh_svc_conf_new["ssh_port"]
            != reboot_test_srv_ssh_svc_conf["ssh_port"]
        )

        wait_docker_service_socket(
            docker_services,
            reboot_test_server.hostname,
            reboot_test_srv_ssh_svc_conf_new["ssh_port"],
        )

        (status, results_info) = ssh_host_service.remote_exec(
            script=["hostname"],
            config=reboot_test_srv_ssh_svc_conf_new,
            env_params={},
        )
        status, results = ssh_host_service.get_remote_exec_results(results_info)
        assert status.is_succeeded()
        assert results["stdout"].strip() == REBOOT_TEST_SERVER_NAME


@requires_docker
def test_ssh_service_reboot(
    locked_docker_services: DockerServices,
    reboot_test_server: SshTestServerInfo,
    ssh_host_service: SshHostService,
) -> None:
    """Test the SshHostService reboot operation."""
    # Grouped together to avoid parallel runner interactions.
    check_ssh_service_reboot(
        locked_docker_services,
        reboot_test_server,
        ssh_host_service,
        graceful=True,
    )
    check_ssh_service_reboot(
        locked_docker_services,
        reboot_test_server,
        ssh_host_service,
        graceful=False,
    )
