#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection FileShare functions for interacting with Azure File Shares.
"""

import os
import logging

from typing import Set

from azure.storage.fileshare import ShareClient

from mlos_bench.service import Service, FileShareService
from mlos_bench.util import check_required_params

_LOG = logging.getLogger(__name__)


class AzureFileShareService(FileShareService):
    """
    Helper methods for interacting with Azure File Share
    """

    _SHARE_URL = "https://{account_name}.file.core.windows.net/{fs_name}"

    def __init__(self, config: dict, parent: Service):
        """
        Create a new file share Service for Azure environments with a given config.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the file share configuration.
            It will be passed as a constructor parameter of the class
            specified by `class_name`.
        parent : Service
            Parent service that can provide mixin functions.
        """
        super().__init__(config, parent)

        check_required_params(
            config, {
                "storageAccountName",
                "storageFileShareName",
                "storageAccountKey",
            }
        )

        self._share_client = ShareClient.from_share_url(
            AzureFileShareService._SHARE_URL.format(
                account_name=config["storageAccountName"],
                fs_name=config["storageFileShareName"],
            ),
            credential=config["storageAccountKey"],
        )

    def download(self, remote_path: str, local_path: str, recursive: bool = True) -> None:
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
                data.readinto(output_file)  # type: ignore[no-untyped-call]

    def upload(self, local_path: str, remote_path: str, recursive: bool = True) -> None:
        super().upload(local_path, remote_path, recursive)
        self._upload(local_path, remote_path, recursive, set())

    def _upload(self, local_path: str, remote_path: str, recursive: bool, seen: Set[str]) -> None:
        """
        Upload contents from a local path to an Azure file share.
        This method is called from `.upload()` above. We need it to avoid exposing
        the `seen` parameter and to make `.upload()` match the base class' virtual
        method.

        Parameters
        ----------
        local_path : str
            Path to the local directory to upload contents from, either a file or directory.
        remote_path : str
            Path in the remote file share to store the uploaded content to.
        recursive : bool
            If False, ignore the subdirectories;
            if True (the default), upload the entire directory tree.
        seen: Set[str]
            Helper set for keeping track of visited directories to break circular paths.
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

    def _remote_makedirs(self, remote_path: str) -> None:
        """
        Create remote directories for the entire path.
        Succeeds even some or all directories along the path already exist.

        Parameters
        ----------
        remote_path : str
            Path in the remote file share to create.
        """
        path = ""
        for folder in remote_path.replace("\\", "/").split("/"):
            if not folder:
                continue
            path += folder + "/"
            dir_client = self._share_client.get_directory_client(path)
            if not dir_client.exists():
                dir_client.create_directory()
