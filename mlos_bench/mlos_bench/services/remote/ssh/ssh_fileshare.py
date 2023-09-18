#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection functions for interacting with SSH servers as file shares.
"""

from enum import Enum
from typing import Optional

import logging

from asyncssh import scp, SFTPError

from mlos_bench.services.base_service import Service
from mlos_bench.services.base_fileshare import FileShareService
from mlos_bench.services.remote.ssh.ssh_service import SshService

_LOG = logging.getLogger(__name__)


class CopyMode(Enum):
    """
    Copy mode enum.
    """

    DOWNLOAD = 1
    UPLOAD = 2


class SshFileShareService(FileShareService, SshService):
    """A collection of functions for interacting with SSH servers as file shares."""

    def __init__(self, config: dict, global_config: dict, parent: Optional[Service]):
        super().__init__(config, global_config, parent)

    async def _start_file_copy(self, params: dict, mode: CopyMode,
                               local_path: str, remote_path: str,
                               recursive: bool = True) -> None:
        """
        Starts a file copy operation

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of parameters (used for establishing the connection).
        mode : CopyMode
            Whether to download or upload the file.
        local_path : str
            Local path to the file/dir.
        remote_path : str
            Remote path to the file/dir.
        recursive : bool, optional
            _description_, by default True

        Raises
        ------
        OSError
            If the local OS returns an error.
        SFTPError
            If the remote OS returns an error.
        """
        connection, _ = await self._get_client_connection(params)
        if mode == CopyMode.DOWNLOAD:
            return await scp(srcpaths=(connection, remote_path), dstpath=local_path, recurse=recursive, preserve=True)
        elif mode == CopyMode.UPLOAD:
            return await scp(srcpaths=local_path, dstpath=(connection, remote_path), recurse=recursive, preserve=True)
        else:
            raise ValueError(f"Unknown copy mode: {mode}")

    def download(self, params: dict, remote_path: str, local_path: str, recursive: bool = True) -> None:
        super().download(params, remote_path, local_path, recursive)
        file_copy_future = self._run_coroutine(
            self._start_file_copy(params, CopyMode.DOWNLOAD, local_path, remote_path, recursive))
        try:
            _ = file_copy_future.result()
        except (OSError, SFTPError) as ex:
            # TODO: Improve error handling:
            raise RuntimeError(f"Failed to download {remote_path} to {local_path} from {params}") from ex

    def upload(self, params: dict, local_path: str, remote_path: str, recursive: bool = True) -> None:
        super().upload(params, local_path, remote_path, recursive)
        file_copy_future = self._run_coroutine(
            self._start_file_copy(params, CopyMode.UPLOAD, local_path, remote_path, recursive))
        try:
            _ = file_copy_future.result()
        except (OSError, SFTPError) as ex:
            # TODO: Improve error handling:
            raise RuntimeError(f"Failed to upload {local_path} to {remote_path} on {params}") from ex
