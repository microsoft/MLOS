#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Common data classes for the SSH service tests."""

import logging
import threading
from dataclasses import dataclass
from subprocess import run
from warnings import warn

# The SSH test server port and name.
# See Also: docker-compose.yml
SSH_TEST_SERVER_PORT = 2254
SSH_TEST_SERVER_NAME = "ssh-server"
ALT_TEST_SERVER_NAME = "alt-server"
REBOOT_TEST_SERVER_NAME = "reboot-server"


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

    def get_port(self, uncached: bool = False) -> int:
        """
        Gets the port that the SSH test server is listening on.

        Note: this value can change when the service restarts so we can't rely on
        the DockerServices.
        """
        thread_id = threading.get_ident()

        warn(
            "[Thread %s] Discovering port for %s (uncached=%s, cached_port=%s)"
            % (thread_id, self.service_name, uncached, self._port),
            UserWarning,
        )

        if self._port is None or uncached:
            try:
                # NOTE: this cache may become stale in another worker if the container restarts in one and the other worker doesn't notice the new port.
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
                warn(
                    "[Thread %s] Port for %s: %s -> %s (uncached=%s)"
                    % (
                        thread_id,
                        self.service_name,
                        old_port,
                        new_port,
                        uncached,
                    ),
                    UserWarning,
                )
            except Exception as e:
                warn(
                    "[Thread %s] Failed to get port for %s: %s"
                    % (
                        thread_id,
                        self.service_name,
                        e,
                    ),
                    UserWarning,
                )
                raise
        else:
            warn(
                "[Thread %s] Using cached port %s for %s"
                % (thread_id, self._port, self.service_name),
                UserWarning,
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

        thread_id = threading.get_ident()

        # Import here to avoid circular imports
        from mlos_bench.tests import check_socket

        is_connectable = check_socket(self.hostname, self._port, timeout)
        if not is_connectable:
            warn(
                "[Thread %s] Connection validation FAILED for %s:%d - port may be stale!"
                % (
                    thread_id,
                    self.service_name,
                    self._port,
                ),
                UserWarning,
            )
        else:
            warn(
                "[Thread %s] Connection validation OK for %s:%d"
                % (
                    thread_id,
                    self.service_name,
                    self._port,
                ),
                UserWarning,
            )
        return is_connectable

    def get_port_with_validation(self, timeout: float = 2.0) -> int:
        """
        Get port with automatic validation and refresh if connection fails.

        This helps detect stale cached ports caused by container restarts.
        """
        thread_id = threading.get_ident()

        # First try cached port
        if self._port is not None:
            if self.validate_connection(timeout):
                return self._port
            else:
                warn(
                    "[Thread %s] Cached port %d for %s failed validation, refreshing..."
                    % (
                        thread_id,
                        self._port,
                        self.service_name,
                    ),
                    UserWarning,
                )
                # Force refresh
                return self.get_port(uncached=True)
        else:
            # No cached port, get fresh one
            return self.get_port(uncached=False)
