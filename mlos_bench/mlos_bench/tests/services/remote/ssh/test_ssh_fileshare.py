#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.remote.ssh.ssh_services
"""

import tempfile

import pytest

from asyncssh import SFTPError

from mlos_bench.environments.status import Status
from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService
from mlos_bench.services.remote.ssh.ssh_fileshare import SshFileShareService

from mlos_bench.tests import requires_docker
from mlos_bench.tests.services.remote.ssh import SshTestServerInfo


@pytest.mark.xdist_group("ssh_test_server")
@requires_docker
def test_ssh_fileshare_single_file(ssh_test_server: SshTestServerInfo,
                                   ssh_fileshare_service: SshFileShareService) -> None:
    """Test the SshFileShareService single file download/upload."""
    config = ssh_test_server.to_ssh_service_config()

    remote_file_path = "/tmp/test_ssh_fileshare_single_file"
    lines = [
        "foo",
        "bar",
    ]
    lines = [line + "\n" for line in lines]

    with tempfile.NamedTemporaryFile(mode='w+t', encoding='utf-8') as temp_file:
        temp_file.writelines(lines)
        temp_file.flush()
        ssh_fileshare_service.upload(
            params=config,
            local_path=temp_file.name,
            remote_path=remote_file_path,
        )

    with tempfile.NamedTemporaryFile() as temp_file:
        ssh_fileshare_service.download(
            params=config,
            remote_path=remote_file_path,
            local_path=temp_file.name,
        )
        # Download will replace the inode at that name, so we need to reopen the file.
        with open(temp_file.name, mode='r', encoding='utf-8') as reopened_temp_file:
            read_lines = reopened_temp_file.readlines()
            assert read_lines == lines


@pytest.mark.xdist_group("ssh_test_server")
@requires_docker
def test_ssh_fileshare_recursive(ssh_test_server: SshTestServerInfo,
                                 ssh_fileshare_service: SshFileShareService) -> None:
    """Test the SshFileShareService recursive download/upload."""
    raise NotImplementedError("TODO")


@pytest.mark.xdist_group("ssh_test_server")
@requires_docker
def test_ssh_fileshare_download_file_dne(ssh_test_server: SshTestServerInfo,
                                         ssh_fileshare_service: SshFileShareService) -> None:
    """Test the SshFileShareService single file download that doesn't exist."""
    config = ssh_test_server.to_ssh_service_config()

    canary_str = "canary"
    with tempfile.NamedTemporaryFile(mode='w+t', encoding='utf-8') as temp_file:
        temp_file.writelines([canary_str])
        temp_file.flush()
        with pytest.raises(SFTPError):
            ssh_fileshare_service.download(
                params=config,
                remote_path="/tmp/file-dne.txt",
                local_path=temp_file.name,
            )
        with open(temp_file.name, mode='r', encoding='utf-8') as reopened_temp_file:
            read_lines = reopened_temp_file.readlines()
            assert read_lines == [canary_str]


@pytest.mark.xdist_group("ssh_test_server")
@requires_docker
def test_ssh_fileshare_upload_file_dne(ssh_test_server: SshTestServerInfo,
                                       ssh_host_service: SshHostService,
                                       ssh_fileshare_service: SshFileShareService) -> None:
    """Test the SshFileShareService single file upload that doesn't exist."""
    config = ssh_test_server.to_ssh_service_config()

    path = '/tmp/upload-file-src-dne.txt'
    with pytest.raises(OSError):
        ssh_fileshare_service.upload(
            params=config,
            remote_path=path,
            local_path=path,
        )
    (status, results) = ssh_host_service.remote_exec(
        script=[f"[[ ! -e {path} ]]; echo $?"],
        config=config,
        env_params={},
    )
    (status, results) = ssh_host_service.get_remote_exec_results(results)
    assert status == Status.SUCCEEDED
    assert str(results["stdout"]).strip() == "0"
