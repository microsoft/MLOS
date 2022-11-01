"""
A collection FileShare functions for interacting with Azure File Shares.
"""

import os
import logging

from typing import Set

from azure.storage.fileshare import ShareClient

from mlos_bench.environment import _check_required_params
from mlos_bench.environment.base_fileshare import FileShareService

_LOG = logging.getLogger(__name__)


class AzureFileShareService(FileShareService):
    """
    Helper methods for interacting with Azure File Shares
    """

    _SHARE_URL = "https://{account_name}.file.core.windows.net/{fs_name}"

    def __init__(self, config):
        """
        Create a new file share with a given config.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the file share configuration.
            It will be passed as a constructor parameter of the class
            specified by `class_name`.
        """
        super().__init__(config)

        _check_required_params(
            config, {
                "storageAccountName",
                "storageFileShareName",
                "storageAccountKey",
                "mountPoint",
            }
        )
        self.account_name = config.get("storageAccountName")
        self.fs_name = config.get("storageFileShareName")
        self.access_key = config.get("storageAccountKey")
        self.mount_point = config.get("mountPoint")
        self._share_client = ShareClient.from_share_url(
            AzureFileShareService._SHARE_URL.format(
                account_name=self.account_name,
                fs_name=self.fs_name,
            ),
            credential=self.access_key,
        )

    def download(self, remote_path: str, local_path: str, recursive: bool = True):
        """
        Downloads contents from an Azure file share path to a local path.

        Parameters
        ----------
        remote_path : str
            Path to download from the remote file share, either a file or directory
        local_path : str
            Path to store the downloaded content to.
        recursive : bool
            To recursively download a directory if True.
        """
        super().download(remote_path, local_path, recursive)
        dir_client = self._share_client.get_directory_client(remote_path)
        if dir_client.exists():
            os.makedirs(local_path, exist_ok=True)
            for content in dir_client.list_directories_and_files():
                name = content["name"]
                local_target = f"{local_path}/{name}"
                remote_target = f"{remote_path}/{name}"
                if recursive or not content["is_directory"]:
                    self.download(remote_target, local_target, recursive)
        else:  # Must be a file
            # Ensure parent folders exist
            folder, _ = os.path.split(local_path)
            os.makedirs(folder, exist_ok=True)

            file_client = self._share_client.get_file_client(remote_path)
            data = file_client.download_file()
            with open(local_path, "wb") as output_file:
                data.readinto(output_file)

    def upload(self, local_path: str, remote_path: str, recursive: bool = True):
        super().upload(local_path, remote_path, recursive)
        self._upload(local_path, remote_path, recursive, set())

    def _remote_makedirs(self, remote_path: str):
        """
        Create remote directories for an entire path if not existing yet.

        Parameters
        ----------
        remote_path : str
            Path in the remote file share to create.
        """
        folders = remote_path.split("/")
        dir_client = None

        for folder in folders:
            # Base case of a folder in root
            if dir_client is None:
                dir_client = self._share_client.get_directory_client(folder)
            else:
                dir_client = dir_client.get_subdirectory_client(folder)

            if not dir_client.exists():
                dir_client.create_directory()

    def _upload(self, local_path: str, remote_path: str, recursive: bool, seen: Set[str]):
        """
        Uploads contents from a local path to an Azure file share path.

        Parameters
        ----------
        local_path : str
            Path to the local directory to upload contents from, either a file or directory.
        remote_path : str
            Path in the remote file share to store the downloaded content to.
        recursive : bool
            To recursively upload a directory if True.
        seen: Optional[Set[str]]
            Helper set for keeping track of visited directories to break circular paths
        """
        local_path = os.path.abspath(local_path)
        if local_path in seen:
            _LOG.warning("Loop in directories, skipping '%s'", local_path)
            return
        seen.add(local_path)

        if os.path.isdir(local_path):
            dir_client = self._share_client.get_directory_client(remote_path)
            if not dir_client.exists():
                dir_client.create_directory()
            for entry in os.scandir(local_path):
                name = entry.name
                local_target = f"{local_path}/{name}"
                remote_target = f"{remote_path}/{name}"
                if recursive or not entry.is_dir():
                    self._upload(local_target, remote_target, recursive, seen)
        else:
            # Ensure parent folders exist
            folder, _ = os.path.split(remote_path)
            self._remote_makedirs(folder)

            file_client = self._share_client.get_file_client(remote_path)
            with open(local_path, "rb") as file_data:
                file_client.upload_file(file_data)
