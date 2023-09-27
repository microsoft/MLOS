#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.remote.ssh.ssh_services
"""

import tempfile

import pytest

from mlos_bench.services.remote.ssh.ssh_fileshare import SshFileShareService

from mlos_bench.tests import requires_docker
from mlos_bench.tests.services.remote.ssh import SshTestServerInfo


@pytest.mark.xdist_group("ssh_test_server")
@requires_docker
def test_ssh_fileshare_single_file(ssh_test_server: SshTestServerInfo,
                                   ssh_fileshare_service: SshFileShareService) -> None:
    """Test the SshFileShareService single file download/upload."""
    config = ssh_test_server.to_ssh_service_config()

    # TODO: Try downloading a file that DNE

    remote_file_path = "/tmp/test_ssh_fileshare_single_file"
    lines = [
        "foo",
        "bar",
    ]

    with tempfile.NamedTemporaryFile(mode='w+t') as temp_file:
        temp_file.seek(0)
        temp_file.writelines(lines)
        ssh_fileshare_service.upload(
            params=config,
            local_path=temp_file.name,
            remote_path=remote_file_path,
        )

    with tempfile.NamedTemporaryFile(mode='w+t') as temp_file:
        ssh_fileshare_service.download(
            params=config,
            remote_path=remote_file_path,
            local_path=temp_file.name,
        )
        temp_file.seek(0)
        assert temp_file.readlines() == lines


@pytest.mark.xdist_group("ssh_test_server")
@requires_docker
def test_ssh_fileshare_recursive(ssh_test_server: SshTestServerInfo,
                                 ssh_fileshare_service: SshFileShareService) -> None:
    """Test the SshFileShareService recursive download/upload."""
    raise NotImplementedError("TODO")
