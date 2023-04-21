# TODO
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for managing hosts via SSH.
"""

import json
import time
import logging

from typing import Callable, Iterable, Tuple

from mlos_bench.environment.status import Status
from mlos_bench.service.base_service import Service
from mlos_bench.service.types.remote_exec_type import SupportsRemoteExec
from mlos_bench.service.types.host_ops_type import SupportsHostOps
from mlos_bench.service.types.os_ops_type import SupportsOSOps
from mlos_bench.util import check_required_params

_LOG = logging.getLogger(__name__)


class SshService(Service, SupportsHostOps, SupportsOSOps, SupportsRemoteExec):
    # pylint: disable=too-many-instance-attributes
    """
    Helper methods to manage VMs on Azure.
    """

