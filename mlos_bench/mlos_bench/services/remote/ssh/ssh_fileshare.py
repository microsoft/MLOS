#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection functions for interacting with SSH servers as file shares.
"""

from enum import Enum
from typing import Optional, Tuple, Union

import logging

from asyncssh import scp, SFTPError, SSHClientConnection

from mlos_bench.services.base_service import Service
from mlos_bench.services.base_fileshare import FileShareService
from mlos_bench.services.remote.ssh.ssh_service import SshService
from mlos_bench.util import merge_parameters

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
        # pylint: disable=too-many-arguments
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
        srcpaths: Union[str, Tuple[SSHClientConnection, str]]
        dstpath: Union[str, Tuple[SSHClientConnection, str]]
        if mode == CopyMode.DOWNLOAD:
            srcpaths = (connection, remote_path)
            dstpath = local_path
        elif mode == CopyMode.UPLOAD:
            srcpaths = local_path
            dstpath = (connection, remote_path)
        else:
            raise ValueError(f"Unknown copy mode: {mode}")
        return await scp(srcpaths=srcpaths, dstpath=dstpath, recurse=recursive, preserve=True)

    def download(self, params: dict, remote_path: str, local_path: str, recursive: bool = True) -> None:
        params = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "ssh_hostname",
            ]
        )
        super().download(params, remote_path, local_path, recursive)
        file_copy_future = self._run_coroutine(
            self._start_file_copy(params, CopyMode.DOWNLOAD, local_path, remote_path, recursive))
        try:
            _ = file_copy_future.result()
        except (OSError, SFTPError) as ex:
            _LOG.error("Failed to download %s to %s from %s: %s", remote_path, local_path, params, ex)
            raise ex

    def upload(self, params: dict, local_path: str, remote_path: str, recursive: bool = True) -> None:
        params = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "ssh_hostname",
            ]
        )
        super().upload(params, local_path, remote_path, recursive)
        file_copy_future = self._run_coroutine(
            self._start_file_copy(params, CopyMode.UPLOAD, local_path, remote_path, recursive))
        try:
            _ = file_copy_future.result()
        except (OSError, SFTPError) as ex:
            _LOG.error("Failed to upload %s to %s on %s: %s", local_path, remote_path, params, ex)
            raise ex