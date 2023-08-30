#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Fixtures for the SSH service tests.
"""

from typing import Tuple

import pytest
from pytest_docker.plugin import Services

from mlos_bench.tests import check_socket, resolve_host_name

# pylint: disable=redefined-outer-name


# The SSH test server port.
# See Also: docker-compose.yml
SSH_TEST_SERVER_PORT = 2254


@pytest.fixture(scope="session")
def ssh_test_server_hostname() -> str:
    """Returns the hostname of the test server."""
    if resolve_host_name('host.docker.internal'):
        return 'host.docker.internal'
    return 'localhost'


@pytest.fixture(scope="session")
def ssh_test_server(ssh_test_server_hostname: str, docker_services: Services) -> Tuple[str, int]:
    """
    Fixture for getting the ssh test server services setup via docker-compose
    using pytest-docker.

    Returns the hostname and port of the test server.
    """
    docker_services.wait_until_responsive(
        check=lambda: check_socket(ssh_test_server_hostname, SSH_TEST_SERVER_PORT),
        timeout=30.0,
        pause=0.5,
    )
    # TODO: Get a copy of the ssh id_rsa key from the test server.
    return (ssh_test_server_hostname, SSH_TEST_SERVER_PORT)
