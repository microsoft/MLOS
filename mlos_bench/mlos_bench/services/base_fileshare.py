#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base class for remote file shares.
"""

import logging

from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Optional

from mlos_bench.services.base_service import Service
from mlos_bench.services.types.fileshare_type import SupportsFileShareOps

_LOG = logging.getLogger(__name__)


class FileShareService(Service, SupportsFileShareOps, metaclass=ABCMeta):
    """
    An abstract base of all file shares.
    """

    def __init__(self, config: dict, global_config: Optional[Dict[str, Any]], parent: Service):
        """
        Create a new file share with a given config.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the file share configuration.
            It will be passed as a constructor parameter of the class
            specified by `class_name`.
        global_config : dict
            Free-format dictionary of global parameters.
        parent : Service
            Parent service that can provide mixin functions.
        """
        super().__init__(config, global_config, parent)

        self.register([
            self.download,
            self.upload,
        ])

    @abstractmethod
    def download(self, remote_path: str, local_path: str, recursive: bool = True) -> None:
        """
        Downloads contents from a remote share path to a local path.

        Parameters
        ----------
        remote_path : str
            Path to download from the remote file share, a file if recursive=False
            or a directory if recursive=True.
        local_path : str
            Path to store the downloaded content to.
        recursive : bool
            If False, ignore the subdirectories;
            if True (the default), download the entire directory tree.
        """
        _LOG.info("Download from File Share %s recursively: %s -> %s",
                  "" if recursive else "non", remote_path, local_path)

    @abstractmethod
    def upload(self, local_path: str, remote_path: str, recursive: bool = True) -> None:
        """
        Uploads contents from a local path to remote share path.

        Parameters
        ----------
        local_path : str
            Path to the local directory to upload contents from.
        remote_path : str
            Path in the remote file share to store the uploaded content to.
        recursive : bool
            If False, ignore the subdirectories;
            if True (the default), upload the entire directory tree.
        """
        _LOG.info("Upload to File Share %s recursively: %s -> %s",
                  "" if recursive else "non", local_path, remote_path)
