#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.remote.ssh.ssh_services
"""

from os.path import basename
from pathlib import Path
from typing import Dict, List

import os
import tempfile

import pytest

from asyncssh import SFTPError

from mlos_bench.environments.status import Status
from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService
from mlos_bench.services.remote.ssh.ssh_fileshare import SshFileShareService
from mlos_bench.util import path_join

from mlos_bench.tests import are_dir_trees_equal, requires_docker
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

    # 1. Write a local file and upload it.

    # NOTE: Since Windows doesn't allow us to reopen the file while it's still
    # open we need to handle deletion ourselves.
    # pylint: disable=consider-using-with
    try:
        temp_file = tempfile.NamedTemporaryFile(mode='w+t', encoding='utf-8', delete=False)
        temp_file.writelines(lines)
        temp_file.flush()
        temp_file.close()

        ssh_fileshare_service.upload(
            params=config,
            local_path=temp_file.name,
            remote_path=remote_file_path,
        )
        os.unlink(temp_file.name)

        # 2. Download the remote file and compare the contents.

        temp_file = tempfile.NamedTemporaryFile(mode='w+t', encoding='utf-8', delete=False)
        temp_file.close()
        ssh_fileshare_service.download(
            params=config,
            remote_path=remote_file_path,
            local_path=temp_file.name,
        )
        # Download will replace the inode at that name, so we need to reopen the file.
        with open(temp_file.name, mode='r', encoding='utf-8') as temp_file_h:
            read_lines = temp_file_h.readlines()
            assert read_lines == lines
    finally:
        os.unlink(temp_file.name)


@pytest.mark.xdist_group("ssh_test_server")
@requires_docker
def test_ssh_fileshare_recursive(ssh_test_server: SshTestServerInfo,
                                 ssh_fileshare_service: SshFileShareService) -> None:
    """Test the SshFileShareService recursive download/upload."""
    config = ssh_test_server.to_ssh_service_config()

    remote_file_path = "/tmp/test_ssh_fileshare_recursive_dir"
    files_lines: Dict[str, List[str]] = {
        "file-a.txt": [
            "a",
            "1",
        ],
        "file-b.txt": [
            "b",
            "2",
        ],
        "subdir/foo.txt": [
            "foo",
            "bar",
        ],
    }
    files_lines = {path: [line + "\n" for line in lines] for (path, lines) in files_lines.items()}

    with tempfile.TemporaryDirectory() as tempdir1, tempfile.TemporaryDirectory() as tempdir2:
        # Setup the directory structure.
        for (file_path, lines) in files_lines.items():
            path = Path(tempdir1, file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, mode='w+t', encoding='utf-8') as temp_file:
                temp_file.writelines(lines)
                temp_file.flush()
            assert os.path.getsize(path) > 0

        # Copy that structure over to the remote server.
        ssh_fileshare_service.upload(
            params=config,
            local_path=f"{tempdir1}",
            remote_path=f"{remote_file_path}",
            recursive=True,
        )

        # Copy the remote structure back to the local machine.
        ssh_fileshare_service.download(
            params=config,
            remote_path=f"{remote_file_path}",
            local_path=f"{tempdir2}",
            recursive=True,
        )

        # Compare both.
        # Note: remote dir name is appended to target.
        assert are_dir_trees_equal(tempdir1, path_join(tempdir2, basename(remote_file_path)))


@pytest.mark.xdist_group("ssh_test_server")
@requires_docker
def test_ssh_fileshare_download_file_dne(ssh_test_server: SshTestServerInfo,
                                         ssh_fileshare_service: SshFileShareService) -> None:
    """Test the SshFileShareService single file download that doesn't exist."""
    config = ssh_test_server.to_ssh_service_config()

    canary_str = "canary"

    try:
        # Windows doesn't allow us to reopen the file while it's still open so we
        # have to reopen it and handle deletion ourselves.
        # pylint: disable=consider-using-with
        temp_file = tempfile.NamedTemporaryFile(mode='w+t', encoding='utf-8', delete=False)
        temp_file.writelines([canary_str])
        temp_file.flush()
        temp_file.close()

        with pytest.raises(SFTPError):
            ssh_fileshare_service.download(
                params=config,
                remote_path="/tmp/file-dne.txt",
                local_path=temp_file.name,
            )
        with open(temp_file.name, mode='r', encoding='utf-8') as temp_file_h:
            read_lines = temp_file_h.readlines()
        assert read_lines == [canary_str]
    finally:
        os.unlink(temp_file.name)


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