#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for mlos_bench sql storage."""

from dataclasses import dataclass
from subprocess import run


# The DB servers' names and other connection info.
# See Also: docker-compose.yml

MYSQL_TEST_SERVER_NAME = "mysql-mlos-bench-server"
PGSQL_TEST_SERVER_NAME = "postgres-mlos-bench-server"

SQL_TEST_SERVER_DATABASE = "mlos_bench"
SQL_TEST_SERVER_PASSWORD = "password"


@dataclass
class SqlTestServerInfo:
    """A data class for SqlTestServerInfo.

    See Also
    --------
    mlos_bench.tests.services.remote.ssh.SshTestServerInfo
    """

    compose_project_name: str
    service_name: str
    hostname: str
    _port: int | None = None

    @property
    def username(self) -> str:
        """Gets the username."""
        usernames = {
            MYSQL_TEST_SERVER_NAME: "root",
            PGSQL_TEST_SERVER_NAME: "postgres",
        }
        return usernames[self.service_name]

    @property
    def password(self) -> str:
        """Gets the password."""
        return SQL_TEST_SERVER_PASSWORD

    @property
    def database(self) -> str:
        """Gets the database."""
        return SQL_TEST_SERVER_DATABASE

    def get_port(self, uncached: bool = False) -> int:
        """
        Gets the port that the SSH test server is listening on.

        Note: this value can change when the service restarts so we can't rely on
        the DockerServices.
        """
        if self._port is None or uncached:
            default_ports = {
                MYSQL_TEST_SERVER_NAME: 3306,
                PGSQL_TEST_SERVER_NAME: 5432,
            }
            default_port = default_ports[self.service_name]
            port_cmd = run(
                (
                    f"docker compose -p {self.compose_project_name} "
                    f"port {self.service_name} {default_port}"
                ),
                shell=True,
                check=True,
                capture_output=True,
            )
            self._port = int(port_cmd.stdout.decode().strip().split(":")[1])
        return self._port
