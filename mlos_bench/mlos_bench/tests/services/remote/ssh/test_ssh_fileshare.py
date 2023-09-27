#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.remote.ssh.ssh_services
"""

from logging import warning
from os.path import basename
from pathlib import Path
from typing import Dict, List

import filecmp
import os
import tempfile

import pytest

from asyncssh import SFTPError

from mlos_bench.environments.status import Status
from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService
from mlos_bench.services.remote.ssh.ssh_fileshare import SshFileShareService
from mlos_bench.util import path_join

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


def are_dir_trees_equal(dir1: str, dir2: str) -> bool:
    """
    Compare two directories recursively. Files in each directory are
    assumed to be equal if their names and contents are equal.

    @param dir1: First directory path
    @param dir2: Second directory path

    @return: True if the directory trees are the same and
        there were no errors while accessing the directories or files,
        False otherwise.
    """
    # See Also: https://stackoverflow.com/a/6681395
    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if len(dirs_cmp.left_only) > 0 or len(dirs_cmp.right_only) > 0 or len(dirs_cmp.funny_files) > 0:
        warning(f"Found differences in dir trees {dir1}, {dir2}:\n{dirs_cmp.diff_files}\n{dirs_cmp.funny_files}")
        return False
    (_, mismatch, errors) = filecmp.cmpfiles(dir1, dir2, dirs_cmp.common_files, shallow=False)
    if len(mismatch) > 0 or len(errors) > 0:
        warning(f"Found differences in files:\n{mismatch}\n{errors}")
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not are_dir_trees_equal(new_dir1, new_dir2):
            return False
    return True


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
