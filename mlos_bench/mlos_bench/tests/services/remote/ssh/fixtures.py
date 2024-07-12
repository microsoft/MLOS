#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Fixtures for the SSH service tests.

Note: these are not in the conftest.py file because they are also used by remote_ssh_env_test.py
"""

import os
import sys
import tempfile
from subprocess import run
from typing import Generator

import pytest
from pytest_docker.plugin import Services as DockerServices

from mlos_bench.services.remote.ssh.ssh_fileshare import SshFileShareService
from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService
from mlos_bench.tests import resolve_host_name
from mlos_bench.tests.services.remote.ssh import (
    ALT_TEST_SERVER_NAME,
    REBOOT_TEST_SERVER_NAME,
    SSH_TEST_SERVER_NAME,
    SshTestServerInfo,
    wait_docker_service_socket,
)

# pylint: disable=redefined-outer-name

HOST_DOCKER_NAME = "host.docker.internal"


@pytest.fixture(scope="session")
def ssh_test_server_hostname() -> str:
    """Returns the local hostname to use to connect to the test ssh server."""
    if sys.platform != "win32" and resolve_host_name(HOST_DOCKER_NAME):
        # On Linux, if we're running in a docker container, we can use the
        # --add-host (extra_hosts in docker-compose.yml) to refer to the host IP.
        return HOST_DOCKER_NAME
    # Docker (Desktop) for Windows (WSL2) uses a special networking magic
    # to refer to the host machine as `localhost` when exposing ports.
    # In all other cases, assume we're executing directly inside conda on the host.
    return "localhost"


@pytest.fixture(scope="session")
def ssh_test_server(
    ssh_test_server_hostname: str,
    docker_compose_project_name: str,
    locked_docker_services: DockerServices,
) -> Generator[SshTestServerInfo, None, None]:
    """
    Fixture for getting the ssh test server services setup via docker-compose using
    pytest-docker.

    Yields the (hostname, port, username, id_rsa_path) of the test server.

    Once the session is over, the docker containers are torn down, and the temporary
    file holding the dynamically generated private key of the test server is deleted.
    """
    # Get a copy of the ssh id_rsa key from the test ssh server.
    with tempfile.NamedTemporaryFile() as id_rsa_file:
        ssh_test_server_info = SshTestServerInfo(
            compose_project_name=docker_compose_project_name,
            service_name=SSH_TEST_SERVER_NAME,
            hostname=ssh_test_server_hostname,
            username="root",
            id_rsa_path=id_rsa_file.name,
        )
        wait_docker_service_socket(
            locked_docker_services, ssh_test_server_info.hostname, ssh_test_server_info.get_port()
        )
        id_rsa_src = f"/{ssh_test_server_info.username}/.ssh/id_rsa"
        docker_cp_cmd = (
            f"docker compose -p {docker_compose_project_name} "
            f"cp {SSH_TEST_SERVER_NAME}:{id_rsa_src} {id_rsa_file.name}"
        )
        cmd = run(
            docker_cp_cmd.split(),
            check=True,
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
        )
        if cmd.returncode != 0:
            raise RuntimeError(
                f"Failed to copy ssh key from {SSH_TEST_SERVER_NAME} container "
                + f"[return={cmd.returncode}]: {str(cmd.stderr)}"
            )
        os.chmod(id_rsa_file.name, 0o600)
        yield ssh_test_server_info
        # NamedTempFile deleted on context exit


@pytest.fixture(scope="session")
def alt_test_server(
    ssh_test_server: SshTestServerInfo,
    locked_docker_services: DockerServices,
) -> SshTestServerInfo:
    """
    Fixture for getting the second ssh test server info from the docker-compose.yml.

    See additional notes in the ssh_test_server fixture above.
    """
    # Note: The alt-server uses the same image as the ssh-server container, so
    # the id_rsa key and username should all match.
    # Only the host port it is allocate is different.
    alt_test_server_info = SshTestServerInfo(
        compose_project_name=ssh_test_server.compose_project_name,
        service_name=ALT_TEST_SERVER_NAME,
        hostname=ssh_test_server.hostname,
        username=ssh_test_server.username,
        id_rsa_path=ssh_test_server.id_rsa_path,
    )
    wait_docker_service_socket(
        locked_docker_services, alt_test_server_info.hostname, alt_test_server_info.get_port()
    )
    return alt_test_server_info


@pytest.fixture(scope="session")
def reboot_test_server(
    ssh_test_server: SshTestServerInfo,
    locked_docker_services: DockerServices,
) -> SshTestServerInfo:
    """
    Fixture for getting the third ssh test server info from the docker-compose.yml.

    See additional notes in the ssh_test_server fixture above.
    """
    # Note: The reboot-server uses the same image as the ssh-server container, so
    # the id_rsa key and username should all match.
    # Only the host port it is allocate is different.
    reboot_test_server_info = SshTestServerInfo(
        compose_project_name=ssh_test_server.compose_project_name,
        service_name=REBOOT_TEST_SERVER_NAME,
        hostname=ssh_test_server.hostname,
        username=ssh_test_server.username,
        id_rsa_path=ssh_test_server.id_rsa_path,
    )
    wait_docker_service_socket(
        locked_docker_services,
        reboot_test_server_info.hostname,
        reboot_test_server_info.get_port(),
    )
    return reboot_test_server_info


@pytest.fixture
def ssh_host_service(ssh_test_server: SshTestServerInfo) -> SshHostService:
    """Generic SshHostService fixture."""
    return SshHostService(
        config={
            "ssh_username": ssh_test_server.username,
            "ssh_priv_key_path": ssh_test_server.id_rsa_path,
        },
    )


@pytest.fixture
def ssh_fileshare_service() -> SshFileShareService:
    """Generic SshFileShareService fixture."""
    return SshFileShareService(
        config={
            # Left blank to make sure we test per connection overrides.
        },
    )
