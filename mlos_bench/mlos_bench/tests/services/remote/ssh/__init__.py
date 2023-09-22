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
