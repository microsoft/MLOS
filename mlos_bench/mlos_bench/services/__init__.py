#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Services for implementing Environments for mlos_bench.

TODO: Improve documentation here.

Overview
--------
TODO: Explain Service mix-ins and how they get used with Environments.

Config
------
TODO: Explain how to configure Services.

See Also
--------
TODO: Provide references to different related classes.
"""

from mlos_bench.services.base_fileshare import FileShareService
from mlos_bench.services.base_service import Service
from mlos_bench.services.local.local_exec import LocalExecService

__all__ = [
    "Service",
    "FileShareService",
    "LocalExecService",
]
