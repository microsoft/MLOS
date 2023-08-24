#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for managing hosts via SSH.
"""

import time
import logging

from typing import Callable, Iterable, Tuple

import asyncssh

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.remote_exec_type import SupportsRemoteExec
from mlos_bench.services.types.host_ops_type import SupportsHostOps
from mlos_bench.services.types.os_ops_type import SupportsOSOps
from mlos_bench.util import check_required_params

_LOG = logging.getLogger(__name__)


class SshService(Service, SupportsOSOps, SupportsRemoteExec):
    """
    Helper methods to manage VMs on Azure.
    """

    _POLL_INTERVAL = 4     # seconds
    _POLL_TIMEOUT = 300    # seconds
    _REQUEST_TIMEOUT = 5   # seconds

    def __init__(self, config: dict, global_config: dict, parent: Service):
        """
        Create a new instance of SSH Service.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration.
        global_config : dict
            Free-format dictionary of global parameters.
        parent : Service
            Parent service that can provide mixin functions.
        """
        super().__init__(config, global_config, parent)

        check_required_params(
            config, {
                "username",
                "hostname",
            }
        )

        # Register methods that we want to expose to the Environment objects.
        self.register([
            self.shutdown,
            self.reboot,
            self.wait_os_operation,
            self.remote_exec,
            self.get_remote_exec_results
        ])

        # These parameters can come from command line as strings, so conversion is needed.
        self._poll_interval = float(config.get("pollInterval", SshService._POLL_INTERVAL))
        self._poll_timeout = float(config.get("pollTimeout", SshService._POLL_TIMEOUT))
        self._request_timeout = float(config.get("requestTimeout", SshService._REQUEST_TIMEOUT))
