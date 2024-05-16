#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""SSH remote service."""

from mlos_bench.services.remote.ssh.ssh_fileshare import SshFileShareService
from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService

__all__ = [
    "SshHostService",
    "SshFileShareService",
]
