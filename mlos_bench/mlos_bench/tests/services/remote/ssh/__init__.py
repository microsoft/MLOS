#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Common data classes for the SSH service tests.
"""

from dataclasses import dataclass


# The SSH test server port and name.
# See Also: docker-compose.yml
SSH_TEST_SERVER_PORT = 2254
SSH_TEST_SERVER_NAME = 'ssh-server'
ALT_TEST_SERVER_NAME = 'alt-server'


@dataclass
class SshTestServerInfo:
    """
    A data class for SshTestServerInfo.
    """

    hostname: str
    port: int
    username: str
    id_rsa_path: str

    def to_ssh_service_config(self) -> dict:
        """Convert to a config dict for SshService."""
        return {
            "ssh_hostname": self.hostname,
            "ssh_port": self.port,
            "ssh_username": self.username,
            "ssh_priv_key_path": self.id_rsa_path,
        }

    def to_connect_params(self) -> dict:
        """
        Convert to a connect_params dict for SshClient.
        See Also: mlos_bench.services.remote.ssh.ssh_service.SshService._get_connect_params()
        """
        return {
            "host": self.hostname,
            "port": self.port,
            "username": self.username,
        }
