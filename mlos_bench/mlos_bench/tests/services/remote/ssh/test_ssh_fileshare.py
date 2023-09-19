#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.remote.ssh.ssh_services
"""

from mlos_bench.services.remote.ssh.ssh_fileshare import SshFileShareService

from mlos_bench.tests import requires_docker
from mlos_bench.tests.services.remote.ssh import SshTestServerInfo


@requires_docker
def test_ssh_fileshare_download(ssh_test_server: SshTestServerInfo, ssh_fileshare_service: SshFileShareService) -> None:
    """Test the SshFileShareService download."""
    raise NotImplementedError("TODO")


@requires_docker
def test_ssh_fileshare_upload(ssh_test_server: SshTestServerInfo, ssh_fileshare_service: SshFileShareService) -> None:
    """Test the SshFileShareService upload."""
    raise NotImplementedError("TODO")
