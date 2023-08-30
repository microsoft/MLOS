#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Fixtures for the SSH service tests.
"""

from typing import Generator, Tuple
from subprocess import run
import tempfile

import os
import sys

import pytest
from pytest_docker.plugin import Services as DockerServices

from mlos_bench.tests import DOCKER, check_socket, resolve_host_name

# pylint: disable=redefined-outer-name


# The SSH test server port.
# See Also: docker-compose.yml
SSH_TEST_SERVER_PORT = 2254


@pytest.fixture(scope="session")
def ssh_test_server_hostname() -> str:
    """Returns the hostname of the test server."""
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
                    docker_services: DockerServices) -> Generator[Tuple[str, int, str, str], None, None]:
    """
    Fixture for getting the ssh test server services setup via docker-compose
    using pytest-docker.

    Yields the (hostname, port, username, id_rsa_path) of the test server.
    """
    # else ...
    docker_services.wait_until_responsive(
        check=lambda: check_socket(ssh_test_server_hostname, SSH_TEST_SERVER_PORT),
        timeout=30.0,
        pause=0.5,
    )
    # Get a copy of the ssh id_rsa key from the test ssh server.
    with tempfile.NamedTemporaryFile() as id_rsa_file:
        username = 'root'
        id_rsa_src = f"/{username}/.ssh/id_rsa"
        docker_cp_cmd = f"docker compose -p {docker_compose_project_name} cp ssh-server:{id_rsa_src} {id_rsa_file.name}"
        docker_cp_cmd_args = docker_cp_cmd.split()
        cmd = run(docker_cp_cmd_args, check=True, cwd=os.path.dirname(__file__), capture_output=True, text=True)
        if cmd.returncode != 0:
            raise RuntimeError(f"Failed to copy ssh key from ssh-server container: {str(cmd.stderr)}")
        os.chmod(id_rsa_file.name, 0o600)
        yield (ssh_test_server_hostname, SSH_TEST_SERVER_PORT, username, id_rsa_file.name)
        # NamedTempFile deleted on context exit
