#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.remote.ssh.ssh_services
"""

from typing import Tuple
from subprocess import run

from mlos_bench.tests import check_socket, resolve_host_name
from mlos_bench.tests import test_requires_docker


@test_requires_docker
def test_ssh_service(ssh_test_server: Tuple[str, int, str, str]) -> None:
    """Test the SSH service."""
    hostname, port, username, id_rsa_path = ssh_test_server
    ip = resolve_host_name(hostname)
    assert ip is not None

    assert check_socket(ip, port)
    ssh_cmd = f"ssh -o StrictHostKeyChecking=accept-new -l {username} -i {id_rsa_path} -p {port} {hostname} hostname"
    ssh_cmd_args = ssh_cmd.split()
    cmd = run(ssh_cmd_args,
              capture_output=True,
              text=True,
              check=True)
    raise Exception(f"{cmd.stdout}")
