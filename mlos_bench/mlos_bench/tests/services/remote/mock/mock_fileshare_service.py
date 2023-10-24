#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for mocking file share ops.
"""

import logging
from typing import Any, Dict, Optional

from mlos_bench.services.base_service import Service
from mlos_bench.services.base_fileshare import FileShareService
from mlos_bench.services.types.fileshare_type import SupportsFileShareOps

_LOG = logging.getLogger(__name__)


class MockFileShareService(FileShareService, SupportsFileShareOps):
    """
    A collection Service functions for mocking file share ops.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None,
                 global_config: Optional[Dict[str, Any]] = None,
                 parent: Optional[Service] = None):
        # IMPORTANT: Save the local methods before invoking the base class constructor
        local_methods = [self.upload, self.download]
        super().__init__(config, global_config, parent)
        self.register(local_methods)

    def download(self, params: dict, remote_path: str, local_path: str, recursive: bool = True) -> None:
        pass

    def upload(self, params: dict, local_path: str, remote_path: str, recursive: bool = True) -> None:
        pass
