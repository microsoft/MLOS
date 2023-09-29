#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Protocol interface for file share operations.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class SupportsFileShareOps(Protocol):
    """
    Protocol interface for file share operations.
    """

    def download(self, params: dict, remote_path: str, local_path: str, recursive: bool = True) -> None:
        """
        Downloads contents from a remote share path to a local path.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of (optional) connection details.
        remote_path : str
            Path to download from the remote file share, a file if recursive=False
            or a directory if recursive=True.
        local_path : str
            Path to store the downloaded content to.
        recursive : bool
            If False, ignore the subdirectories;
            if True (the default), download the entire directory tree.
        """

    def upload(self, params: dict, local_path: str, remote_path: str, recursive: bool = True) -> None:
        """
        Uploads contents from a local path to remote share path.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of (optional) connection details.
        local_path : str
            Path to the local directory to upload contents from.
        remote_path : str
            Path in the remote file share to store the uploaded content to.
        recursive : bool
            If False, ignore the subdirectories;
            if True (the default), upload the entire directory tree.
        """
