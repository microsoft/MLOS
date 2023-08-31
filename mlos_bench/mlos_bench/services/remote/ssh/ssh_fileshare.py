#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection functions for interacting with SSH servers as file shares.
"""

import logging

import asyncssh

from mlos_bench.services.base_service import Service
from mlos_bench.services.base_fileshare import FileShareService
from mlos_bench.services.remote.ssh.ssh_service import SshService
from mlos_bench.util import check_required_params

_LOG = logging.getLogger(__name__)


class SshFileShareService(FileShareService, SshService):
    """A collection of functions for interacting with SSH servers as file shares."""

    def __init__(self, config: dict, global_config: dict, parent: Service):
        # TODO: double-check multi-inheritance
        super().__init__(config, global_config, parent)
        raise NotImplementedError("TODO")

    def upload(self, local_path: str, remote_path: str, recursive: bool = True) -> None:
        raise NotImplementedError("TODO")

    def download(self, remote_path: str, local_path: str, recursive: bool = True) -> None:
        raise NotImplementedError("TODO")
