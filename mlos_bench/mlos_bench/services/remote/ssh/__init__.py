#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""SSH remote service."""

from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService
from mlos_bench.services.remote.ssh.ssh_fileshare import SshFileShareService

__all__ = [
    "SshHostService",
    "SshFileShareService",
]
