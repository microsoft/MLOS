#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Remote VM (Host) Environment."""

import logging

from mlos_bench.environments.remote.host_env import HostEnv

_LOG = logging.getLogger(__name__)


class VMEnv(HostEnv):
    """
    Remote VM/host environment.

    Note: this is just a class alias for HostEnv for historical purposes.
    """
