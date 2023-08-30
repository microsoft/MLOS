#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.remote.ssh.ssh_services
"""

from typing import Tuple

from mlos_bench.tests import check_socket, resolve_host_name

def test_ssh_service(ssh_test_server: Tuple[str, int]) -> None:
    """Test the SSH service."""
    hostname, port = ssh_test_server
    ip = resolve_host_name(hostname)
    assert ip is not None
    assert check_socket(ip, port)
    raise Exception(f"hostname: {hostname}, ip: {ip}, port: {port}")
