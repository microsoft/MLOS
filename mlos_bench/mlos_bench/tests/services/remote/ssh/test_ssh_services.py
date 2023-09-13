#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.remote.ssh.ssh_services
"""

from typing import Tuple
from subprocess import run

from mlos_bench.tests import requires_docker, check_socket, resolve_host_name
from mlos_bench.tests.services.remote.ssh import SshTestServerInfo


@requires_docker
def test_ssh_service(ssh_test_server_info: SshTestServerInfo) -> None:
    """Test the SSH service."""
    ip_addr = resolve_host_name(ssh_test_server_info.hostname)
    assert ip_addr is not None

    assert check_socket(ip_addr, ssh_test_server_info.port)
    ssh_cmd = "ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new " \
        + f"-l {ssh_test_server_info.username} -i {ssh_test_server_info.id_rsa_path} " \
        + f"-p {ssh_test_server_info.port} {ssh_test_server_info.hostname} hostname"
    cmd = run(ssh_cmd.split(),
              capture_output=True,
              text=True,
              check=True)
    raise NotImplementedError(f"TODO: container hostname = {cmd.stdout}")
