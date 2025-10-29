#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Common data classes for the SSH service tests."""

import logging
from dataclasses import dataclass
from subprocess import run

from mlos_bench.tests import check_socket
from mlos_bench.tests.docker_fixtures_util import wait_docker_service_healthy

# The SSH test server port and name.
# See Also: docker-compose.yml
SSH_TEST_SERVER_PORT = 2254
SSH_TEST_SERVER_NAME = "ssh-server"
ALT_TEST_SERVER_NAME = "alt-server"
REBOOT_TEST_SERVER_NAME = "reboot-server"

_LOG = logging.getLogger(__name__)


@dataclass
class SshTestServerInfo:
    """
    A data class for SshTestServerInfo.

    See Also
    --------
    mlos_bench.tests.storage.sql.SqlTestServerInfo
    """

    compose_project_name: str
    service_name: str
    hostname: str
    username: str
    id_rsa_path: str
    _port: int | None = None

    def get_port(self, uncached: bool = False, check_port: bool = True) -> int:
        """
        Gets the port that the SSH test server is listening on.

        Note: this value can change when the service restarts so we can't rely on
        the DockerServices.
        """
        if not uncached and self._port is not None:
            # NOTE: this cache may become stale in another worker if the
            # container restarts in one and the other worker doesn't notice the new port.
            # Optionally check the status of the cached port before returning it.
            if not check_port or self.validate_connection():
                _LOG.debug(
                    "Using cached port %s for %s %s validation.",
                    self._port,
                    self.service_name,
                    "with" if check_port else "without",
                )
                return self._port

        # Check container state before proceeding to avoid a race in docker
        # container startup.
        _LOG.info(
            (
                "Discovering port for %s (uncached=%s, cached_port=%s) "
                "after waiting for container readiness."
            ),
            self.service_name,
            uncached,
            self._port,
        )
        wait_docker_service_healthy(
            self.compose_project_name,
            self.service_name,
        )
        _LOG.debug("Container %s is healthy, getting port...", self.service_name)

        port_cmd = run(
            (
                f"docker compose -p {self.compose_project_name} "
                f"port {self.service_name} {SSH_TEST_SERVER_PORT}"
            ),
            shell=True,
            check=True,
            capture_output=True,
        )
        new_port = int(port_cmd.stdout.decode().strip().split(":")[1])
        old_port = self._port
        self._port = new_port
        _LOG.info(
            "Port for %s: %s -> %s (uncached=%s)",
            self.service_name,
            old_port,
            new_port,
            uncached,
        )
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

    def validate_connection(self, timeout: float = 2.0) -> bool:
        """
        Validate that the current cached port is still connectable.

        Returns False if the connection fails, indicating the port may be stale.
        """
        if self._port is None:
            return False

        is_connectable = check_socket(self.hostname, self._port, timeout)
        if not is_connectable:
            _LOG.warning(
                "Connection validation FAILED for %s:%d - port may be stale!",
                self.service_name,
                self._port,
            )
        else:
            _LOG.debug(
                "Connection validation OK for %s:%d",
                self.service_name,
                self._port,
            )
        return is_connectable
