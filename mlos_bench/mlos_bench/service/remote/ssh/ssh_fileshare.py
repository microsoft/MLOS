#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection FileShare functions for interacting with SSH servers as file shares.
"""

import os
import logging

from typing import Set

import asyncssh

from mlos_bench.service.base_service import Service
from mlos_bench.service.base_fileshare import FileShareService
from mlos_bench.util import check_required_params

_LOG = logging.getLogger(__name__)


class SshFileShareService(FileShareService):
    # TODO
