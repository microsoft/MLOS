#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for mlos_bench.services.remote.azure.azure_fileshare."""

import os
from unittest.mock import MagicMock, Mock, call, patch

from mlos_bench.services.remote.azure.azure_fileshare import AzureFileShareService

# pylint: disable=missing-function-docstring
# pylint: disable=too-many-arguments
# pylint: disable=unused-argument


@patch("mlos_bench.services.remote.azure.azure_fileshare.open")
@patch("mlos_bench.services.remote.azure.azure_fileshare.os.makedirs")
def test_download_file(
    mock_makedirs: MagicMock,
    mock_open: MagicMock,
    azure_fileshare: AzureFileShareService,
) -> None:
    filename = "test.csv"
    remote_folder = "a/remote/folder"
    local_folder = "some/local/folder"
    remote_path = f"{remote_folder}/{filename}"
    local_path = f"{local_folder}/{filename}"
    mock_share_client = azure_fileshare._share_client  # pylint: disable=protected-access
    config: dict = {}
    with patch.object(mock_share_client, "get_file_client") as mock_get_file_client, patch.object(
        mock_share_client, "get_directory_client"
    ) as mock_get_directory_client:
        mock_get_directory_client.return_value = Mock(exists=Mock(return_value=False))

        azure_fileshare.download(config, remote_path, local_path)

        mock_get_file_client.assert_called_with(remote_path)

        mock_makedirs.assert_called_with(
            local_folder,
            exist_ok=True,
        )
        open_path, open_mode = mock_open.call_args.args
        assert os.path.abspath(local_path) == os.path.abspath(open_path)
        assert open_mode == "wb"


def make_dir_client_returns(remote_folder: str) -> dict:
    return {
        remote_folder: Mock(
            exists=Mock(return_value=True),
            list_directories_and_files=Mock(
                return_value=[
                    {"name": "a_folder", "is_directory": True},
                    {"name": "a_file_1.csv", "is_directory": False},
                ]
            ),
        ),
        f"{remote_folder}/a_folder": Mock(
            exists=Mock(return_value=True),
            list_directories_and_files=Mock(
                return_value=[
                    {"name": "a_file_2.csv", "is_directory": False},
                ]
            ),
        ),
        f"{remote_folder}/a_file_1.csv": Mock(exists=Mock(return_value=False)),
        f"{remote_folder}/a_folder/a_file_2.csv": Mock(exists=Mock(return_value=False)),
    }


@patch("mlos_bench.services.remote.azure.azure_fileshare.open")
@patch("mlos_bench.services.remote.azure.azure_fileshare.os.makedirs")
def test_download_folder_non_recursive(
    mock_makedirs: MagicMock,
    mock_open: MagicMock,
    azure_fileshare: AzureFileShareService,
) -> None:
    remote_folder = "a/remote/folder"
    local_folder = "some/local/folder"
    dir_client_returns = make_dir_client_returns(remote_folder)
    mock_share_client = azure_fileshare._share_client  # pylint: disable=protected-access
    config: dict = {}
    with patch.object(
        mock_share_client, "get_directory_client"
    ) as mock_get_directory_client, patch.object(
        mock_share_client, "get_file_client"
    ) as mock_get_file_client:

        mock_get_directory_client.side_effect = lambda x: dir_client_returns[x]

        azure_fileshare.download(config, remote_folder, local_folder, recursive=False)

    mock_get_file_client.assert_called_with(
        f"{remote_folder}/a_file_1.csv",
    )
    mock_get_directory_client.assert_has_calls(
        [
            call(remote_folder),
            call(f"{remote_folder}/a_file_1.csv"),
        ],
        any_order=True,
    )


@patch("mlos_bench.services.remote.azure.azure_fileshare.open")
@patch("mlos_bench.services.remote.azure.azure_fileshare.os.makedirs")
def test_download_folder_recursive(
    mock_makedirs: MagicMock,
    mock_open: MagicMock,
    azure_fileshare: AzureFileShareService,
) -> None:
    remote_folder = "a/remote/folder"
    local_folder = "some/local/folder"
    dir_client_returns = make_dir_client_returns(remote_folder)
    mock_share_client = azure_fileshare._share_client  # pylint: disable=protected-access
    config: dict = {}
    with patch.object(
        mock_share_client, "get_directory_client"
    ) as mock_get_directory_client, patch.object(
        mock_share_client, "get_file_client"
    ) as mock_get_file_client:
        mock_get_directory_client.side_effect = lambda x: dir_client_returns[x]

        azure_fileshare.download(config, remote_folder, local_folder, recursive=True)

    mock_get_file_client.assert_has_calls(
        [
            call(f"{remote_folder}/a_file_1.csv"),
            call(f"{remote_folder}/a_folder/a_file_2.csv"),
        ],
        any_order=True,
    )
    mock_get_directory_client.assert_has_calls(
        [
            call(remote_folder),
            call(f"{remote_folder}/a_file_1.csv"),
            call(f"{remote_folder}/a_folder"),
            call(f"{remote_folder}/a_folder/a_file_2.csv"),
        ],
        any_order=True,
    )


@patch("mlos_bench.services.remote.azure.azure_fileshare.open")
@patch("mlos_bench.services.remote.azure.azure_fileshare.os.path.isdir")
def test_upload_file(
    mock_isdir: MagicMock,
    mock_open: MagicMock,
    azure_fileshare: AzureFileShareService,
) -> None:
    filename = "test.csv"
    remote_folder = "a/remote/folder"
    local_folder = "some/local/folder"
    remote_path = f"{remote_folder}/{filename}"
    local_path = f"{local_folder}/{filename}"
    mock_share_client = azure_fileshare._share_client  # pylint: disable=protected-access
    mock_isdir.return_value = False
    config: dict = {}

    with patch.object(mock_share_client, "get_file_client") as mock_get_file_client:
        azure_fileshare.upload(config, local_path, remote_path)

    mock_get_file_client.assert_called_with(remote_path)
    open_path, open_mode = mock_open.call_args.args
    assert os.path.abspath(local_path) == os.path.abspath(open_path)
    assert open_mode == "rb"


class MyDirEntry:
    # pylint: disable=too-few-public-methods
    """Dummy class for os.DirEntry."""

    def __init__(self, name: str, is_a_dir: bool):
        self.name = name
        self.is_a_dir = is_a_dir

    def is_dir(self) -> bool:
        return self.is_a_dir


def make_scandir_returns(local_folder: str) -> dict:
    return {
        local_folder: [
            MyDirEntry("a_folder", True),
            MyDirEntry("a_file_1.csv", False),
        ],
        f"{local_folder}/a_folder": [
            MyDirEntry("a_file_2.csv", False),
        ],
    }


def make_isdir_returns(local_folder: str) -> dict:
    return {
        local_folder: True,
        f"{local_folder}/a_file_1.csv": False,
        f"{local_folder}/a_folder": True,
        f"{local_folder}/a_folder/a_file_2.csv": False,
    }


def process_paths(input_path: str) -> str:
    skip_prefix = os.getcwd()
    # Remove prefix from os.path.abspath if there
    if input_path == os.path.abspath(input_path):
        result = input_path[(len(skip_prefix) + 1) :]
    else:
        result = input_path
    # Change file seps to unix-style
    return result.replace("\\", "/")


@patch("mlos_bench.services.remote.azure.azure_fileshare.open")
@patch("mlos_bench.services.remote.azure.azure_fileshare.os.path.isdir")
@patch("mlos_bench.services.remote.azure.azure_fileshare.os.scandir")
def test_upload_directory_non_recursive(
    mock_scandir: MagicMock,
    mock_isdir: MagicMock,
    mock_open: MagicMock,
    azure_fileshare: AzureFileShareService,
) -> None:
    remote_folder = "a/remote/folder"
    local_folder = "some/local/folder"
    scandir_returns = make_scandir_returns(local_folder)
    isdir_returns = make_isdir_returns(local_folder)
    mock_scandir.side_effect = lambda x: scandir_returns[process_paths(x)]
    mock_isdir.side_effect = lambda x: isdir_returns[process_paths(x)]
    mock_share_client = azure_fileshare._share_client  # pylint: disable=protected-access
    config: dict = {}

    with patch.object(mock_share_client, "get_file_client") as mock_get_file_client:
        azure_fileshare.upload(config, local_folder, remote_folder, recursive=False)

    mock_get_file_client.assert_called_with(f"{remote_folder}/a_file_1.csv")


@patch("mlos_bench.services.remote.azure.azure_fileshare.open")
@patch("mlos_bench.services.remote.azure.azure_fileshare.os.path.isdir")
@patch("mlos_bench.services.remote.azure.azure_fileshare.os.scandir")
def test_upload_directory_recursive(
    mock_scandir: MagicMock,
    mock_isdir: MagicMock,
    mock_open: MagicMock,
    azure_fileshare: AzureFileShareService,
) -> None:
    remote_folder = "a/remote/folder"
    local_folder = "some/local/folder"
    scandir_returns = make_scandir_returns(local_folder)
    isdir_returns = make_isdir_returns(local_folder)
    mock_scandir.side_effect = lambda x: scandir_returns[process_paths(x)]
    mock_isdir.side_effect = lambda x: isdir_returns[process_paths(x)]
    mock_share_client = azure_fileshare._share_client  # pylint: disable=protected-access
    config: dict = {}

    with patch.object(mock_share_client, "get_file_client") as mock_get_file_client:
        azure_fileshare.upload(config, local_folder, remote_folder, recursive=True)

    mock_get_file_client.assert_has_calls(
        [
            call(f"{remote_folder}/a_file_1.csv"),
            call(f"{remote_folder}/a_folder/a_file_2.csv"),
        ],
        any_order=True,
    )
