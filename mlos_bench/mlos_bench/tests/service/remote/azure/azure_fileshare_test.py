"""
Tests for mlos_bench.service.remote.azure.azure_fileshare
"""

import os
from unittest.mock import Mock, patch, call

# pylint: disable=missing-function-docstring
# pylint: disable=too-many-arguments
# pylint: disable=unused-argument


@patch("mlos_bench.service.remote.azure.azure_fileshare.open")
@patch("mlos_bench.service.remote.azure.azure_fileshare.os.makedirs")
def test_download_file(mock_makedirs, mock_open, azure_fileshare):
    filename = "test.csv"
    remote_folder = "a/remote/folder"
    local_folder = "some/local/folder"
    remote_path = f"{remote_folder}/{filename}"
    local_path = f"{local_folder}/{filename}"
    # pylint: disable=protected-access
    mock_share_client = azure_fileshare._share_client
    mock_share_client.get_directory_client.return_value = Mock(
        exists=Mock(return_value=False)
    )

    azure_fileshare.download(remote_path, local_path)

    mock_share_client.get_file_client.assert_called_with(remote_path)
    mock_makedirs.assert_called_with(
        local_folder,
        exist_ok=True,
    )
    open_path, open_mode = mock_open.call_args.args
    assert os.path.abspath(local_path) == os.path.abspath(open_path)
    assert open_mode == "wb"


def make_dir_client_returns(remote_folder: str):
    return {
        remote_folder: Mock(
            exists=Mock(return_value=True),
            list_directories_and_files=Mock(return_value=[
                {"name": "a_folder", "is_directory": True},
                {"name": "a_file_1.csv", "is_directory": False},
            ])
        ),
        f"{remote_folder}/a_folder": Mock(
            exists=Mock(return_value=True),
            list_directories_and_files=Mock(return_value=[
                {"name": "a_file_2.csv", "is_directory": False},
            ])
        ),
        f"{remote_folder}/a_file_1.csv": Mock(
            exists=Mock(return_value=False)
        ),
        f"{remote_folder}/a_folder/a_file_2.csv": Mock(
            exists=Mock(return_value=False)
        ),
    }


@patch("mlos_bench.service.remote.azure.azure_fileshare.open")
@patch("mlos_bench.service.remote.azure.azure_fileshare.os.makedirs")
def test_download_folder_non_recursive(mock_makedirs, mock_open, azure_fileshare):
    remote_folder = "a/remote/folder"
    local_folder = "some/local/folder"
    dir_client_returns = make_dir_client_returns(remote_folder)
    # pylint: disable=protected-access
    mock_share_client = azure_fileshare._share_client
    mock_share_client.get_directory_client.side_effect = lambda x: dir_client_returns[x]

    azure_fileshare.download(remote_folder, local_folder, recursive=False)

    mock_share_client.get_file_client.assert_called_with(
        f"{remote_folder}/a_file_1.csv",
    )
    mock_share_client.get_directory_client.assert_has_calls([
        call(remote_folder),
        call(f"{remote_folder}/a_file_1.csv"),
    ], any_order=True)


@patch("mlos_bench.service.remote.azure.azure_fileshare.open")
@patch("mlos_bench.service.remote.azure.azure_fileshare.os.makedirs")
def test_download_folder_recursive(mock_makedirs, mock_open, azure_fileshare):
    remote_folder = "a/remote/folder"
    local_folder = "some/local/folder"
    dir_client_returns = make_dir_client_returns(remote_folder)
    # pylint: disable=protected-access
    mock_share_client = azure_fileshare._share_client
    mock_share_client.get_directory_client.side_effect = lambda x: dir_client_returns[x]

    azure_fileshare.download(remote_folder, local_folder, recursive=True)

    mock_share_client.get_file_client.assert_has_calls([
        call(f"{remote_folder}/a_file_1.csv"),
        call(f"{remote_folder}/a_folder/a_file_2.csv"),
    ], any_order=True)
    mock_share_client.get_directory_client.assert_has_calls([
        call(remote_folder),
        call(f"{remote_folder}/a_file_1.csv"),
        call(f"{remote_folder}/a_folder"),
        call(f"{remote_folder}/a_folder/a_file_2.csv"),
    ], any_order=True)


@patch("mlos_bench.service.remote.azure.azure_fileshare.open")
@patch("mlos_bench.service.remote.azure.azure_fileshare.os.path.isdir")
def test_upload_file(mock_isdir, mock_open, azure_fileshare):
    filename = "test.csv"
    remote_folder = "a/remote/folder"
    local_folder = "some/local/folder"
    remote_path = f"{remote_folder}/{filename}"
    local_path = f"{local_folder}/{filename}"
    # pylint: disable=protected-access
    mock_share_client = azure_fileshare._share_client
    mock_isdir.return_value = False

    azure_fileshare.upload(local_path, remote_path)

    mock_share_client.get_file_client.assert_called_with(remote_path)
    open_path, open_mode = mock_open.call_args.args
    assert os.path.abspath(local_path) == os.path.abspath(open_path)
    assert open_mode == "rb"


class MyDirEntry:
    # pylint: disable=too-few-public-methods
    """Dummy class for os.DirEntry"""
    def __init__(self, name: str, is_a_dir: bool):
        self.name = name
        self.is_a_dir = is_a_dir

    def is_dir(self):
        return self.is_a_dir


def make_scandir_returns(local_folder: str):
    return {
        local_folder: [
            MyDirEntry("a_folder", True),
            MyDirEntry("a_file_1.csv", False),
        ],
        f"{local_folder}/a_folder": [
            MyDirEntry("a_file_2.csv", False),
        ],
    }


def make_isdir_returns(local_folder: str):
    return {
        local_folder: True,
        f"{local_folder}/a_file_1.csv": False,
        f"{local_folder}/a_folder": True,
        f"{local_folder}/a_folder/a_file_2.csv": False,
    }


def process_paths(input_path):
    skip_prefix = os.getcwd()
    # Remove prefix from os.path.abspath if there
    if input_path == os.path.abspath(input_path):
        result = input_path[len(skip_prefix) + 1:]
    else:
        result = input_path
    # Change file seps to unix-style
    return result.replace("\\", "/")


@patch("mlos_bench.service.remote.azure.azure_fileshare.open")
@patch("mlos_bench.service.remote.azure.azure_fileshare.os.path.isdir")
@patch("mlos_bench.service.remote.azure.azure_fileshare.os.scandir")
def test_upload_directory_non_recursive(mock_scandir, mock_isdir, mock_open, azure_fileshare):
    remote_folder = "a/remote/folder"
    local_folder = "some/local/folder"
    scandir_returns = make_scandir_returns(local_folder)
    isdir_returns = make_isdir_returns(local_folder)
    mock_scandir.side_effect = lambda x: scandir_returns[process_paths(x)]
    mock_isdir.side_effect = lambda x: isdir_returns[process_paths(x)]
    # pylint: disable=protected-access
    mock_share_client = azure_fileshare._share_client

    azure_fileshare.upload(local_folder, remote_folder, recursive=False)

    mock_share_client.get_file_client.assert_called_with(f"{remote_folder}/a_file_1.csv")


@patch("mlos_bench.service.remote.azure.azure_fileshare.open")
@patch("mlos_bench.service.remote.azure.azure_fileshare.os.path.isdir")
@patch("mlos_bench.service.remote.azure.azure_fileshare.os.scandir")
def test_upload_directory_recursive(mock_scandir, mock_isdir, mock_open, azure_fileshare):
    remote_folder = "a/remote/folder"
    local_folder = "some/local/folder"
    scandir_returns = make_scandir_returns(local_folder)
    isdir_returns = make_isdir_returns(local_folder)
    mock_scandir.side_effect = lambda x: scandir_returns[process_paths(x)]
    mock_isdir.side_effect = lambda x: isdir_returns[process_paths(x)]
    # pylint: disable=protected-access
    mock_share_client = azure_fileshare._share_client

    azure_fileshare.upload(local_folder, remote_folder, recursive=True)

    mock_share_client.get_file_client.assert_has_calls([
        call(f"{remote_folder}/a_file_1.csv"),
        call(f"{remote_folder}/a_folder/a_file_2.csv"),
    ], any_order=True)
