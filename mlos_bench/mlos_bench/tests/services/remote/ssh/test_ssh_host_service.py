#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.remote.ssh.ssh_host_service
"""

from subprocess import run

from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService

from mlos_bench.tests import requires_docker, check_socket, resolve_host_name
from mlos_bench.tests.services.remote.ssh import SshTestServerInfo


@requires_docker
def test_ssh_service_remote_exec(ssh_test_server: SshTestServerInfo, ssh_host_service: SshHostService) -> None:
    """Test the SshHostService remote_exec."""
    raise NotImplementedError("TODO")
