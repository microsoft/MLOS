#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Common data classes for the SSH service tests."""

from dataclasses import dataclass
from subprocess import run
from typing import Optional

from pytest_docker.plugin import Services as DockerServices

from mlos_bench.tests import check_socket

# The SSH test server port and name.
# See Also: docker-compose.yml
SSH_TEST_SERVER_PORT = 2254
SSH_TEST_SERVER_NAME = "ssh-server"
ALT_TEST_SERVER_NAME = "alt-server"
REBOOT_TEST_SERVER_NAME = "reboot-server"


@dataclass
class SshTestServerInfo:
    """A data class for SshTestServerInfo."""

    compose_project_name: str
    service_name: str
    hostname: str
    username: str
    id_rsa_path: str
    _port: Optional[int] = None

    def get_port(self, uncached: bool = False) -> int:
        """
        Gets the port that the SSH test server is listening on.

        Note: this value can change when the service restarts so we can't rely on
        the DockerServices.
        """
        if self._port is None or uncached:
            port_cmd = run(
                (
                    f"docker compose -p {self.compose_project_name} "
                    f"port {self.service_name} {SSH_TEST_SERVER_PORT}"
                ),
                shell=True,
                check=True,
                capture_output=True,
            )
            self._port = int(port_cmd.stdout.decode().strip().split(":")[1])
        return self._port

    def to_ssh_service_config(self, uncached: bool = False) -> dict:
        """Convert to a config dict for SshService."""
        return {
            "ssh_hostname": self.hostname,
            "ssh_port": self.get_port(uncached),
            "ssh_username": self.username,
            "ssh_priv_key_path": self.id_rsa_path,
        }

    def to_connect_params(self, uncached: bool = False) -> dict:
        """
        Convert to a connect_params dict for SshClient.

        See Also: mlos_bench.services.remote.ssh.ssh_service.SshService._get_connect_params()
        """
        return {
            "host": self.hostname,
            "port": self.get_port(uncached),
            "username": self.username,
        }


def wait_docker_service_socket(docker_services: DockerServices, hostname: str, port: int) -> None:
    """Wait until a docker service is ready."""
    docker_services.wait_until_responsive(
        check=lambda: check_socket(hostname, port),
        timeout=30.0,
        pause=0.5,
    )
