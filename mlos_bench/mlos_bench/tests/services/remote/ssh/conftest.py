#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Fixtures for the SSH service tests.
"""

from typing import Generator
from subprocess import run
import tempfile

import os
import sys

import pytest
from pytest_docker.plugin import Services as DockerServices

from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService
from mlos_bench.services.remote.ssh.ssh_fileshare import SshFileShareService

from mlos_bench.tests import check_socket, resolve_host_name
from mlos_bench.tests.services.remote.ssh import SSH_TEST_SERVER_NAME, SSH_TEST_SERVER_PORT, SshTestServerInfo

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="session")
def ssh_test_server_hostname() -> str:
    """Returns the local hostname to use to connect to the test ssh server."""
    if sys.platform == 'win32':
        # Docker (Desktop) for Windows (WSL2) uses a special networking magic
        # to refer to the host machine when exposing ports.
        return 'localhost'
    # On Linux, if we're running in a docker container, we can use the
    # --add-host (extra_hosts in docker-compose.yml) to refer to the host IP.
    if resolve_host_name('host.docker.internal'):
        return 'host.docker.internal'
    # Otherwise, assume we're executing directly inside conda on the host.
    return 'localhost'


@pytest.fixture(scope="session")
def ssh_test_server(ssh_test_server_hostname: str,
                    docker_compose_project_name: str,
                    docker_services: DockerServices) -> Generator[SshTestServerInfo, None, None]:
    """
    Fixture for getting the ssh test server services setup via docker-compose
    using pytest-docker.

    Yields the (hostname, port, username, id_rsa_path) of the test server.

    Once the session is over, the docker containers are torn down, and the
    temporary file holding the dynamically generated private key of the test
    server is deleted.
    """
    # else ...
    local_port = docker_services.port_for(SSH_TEST_SERVER_NAME, SSH_TEST_SERVER_PORT)
    docker_services.wait_until_responsive(
        check=lambda: check_socket(ssh_test_server_hostname, local_port),
        timeout=30.0,
        pause=0.5,
    )
    # Get a copy of the ssh id_rsa key from the test ssh server.
    with tempfile.NamedTemporaryFile() as id_rsa_file:
        username = 'root'
        id_rsa_src = f"/{username}/.ssh/id_rsa"
        docker_cp_cmd = f"docker compose -p {docker_compose_project_name} cp {SSH_TEST_SERVER_NAME}:{id_rsa_src} {id_rsa_file.name}"
        cmd = run(docker_cp_cmd.split(), check=True, cwd=os.path.dirname(__file__), capture_output=True, text=True)
        if cmd.returncode != 0:
            raise RuntimeError(f"Failed to copy ssh key from {SSH_TEST_SERVER_NAME} container: {str(cmd.stderr)}")
        os.chmod(id_rsa_file.name, 0o600)
        yield SshTestServerInfo(
            hostname=ssh_test_server_hostname,
            port=local_port,
            username=username,
            id_rsa_path=id_rsa_file.name)
        # NamedTempFile deleted on context exit


@pytest.fixture
def ssh_host_service() -> SshHostService:
    """Generic SshHostService fixture."""
    return SshHostService(
        config={},
        global_config={},
        parent=None,
    )


@pytest.fixture
def ssh_fileshare_service() -> SshFileShareService:
    """Generic SshFileShareService fixture."""
    return SshFileShareService(
        config={},
        global_config={},
        parent=None,
    )
