#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A collection Service functions for mocking file share ops."""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from mlos_bench.services.base_fileshare import FileShareService
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.fileshare_type import SupportsFileShareOps

_LOG = logging.getLogger(__name__)


class MockFileShareService(FileShareService, SupportsFileShareOps):
    """A collection Service functions for mocking file share ops."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        global_config: Optional[Dict[str, Any]] = None,
        parent: Optional[Service] = None,
        methods: Union[Dict[str, Callable], List[Callable], None] = None,
    ):
        super().__init__(
            config,
            global_config,
            parent,
            self.merge_methods(methods, [self.upload, self.download]),
        )
        self._upload: List[Tuple[str, str]] = []
        self._download: List[Tuple[str, str]] = []

    def upload(
        self,
        params: dict,
        local_path: str,
        remote_path: str,
        recursive: bool = True,
    ) -> None:
        self._upload.append((local_path, remote_path))

    def download(
        self,
        params: dict,
        remote_path: str,
        local_path: str,
        recursive: bool = True,
    ) -> None:
        self._download.append((remote_path, local_path))

    def get_upload(self) -> List[Tuple[str, str]]:
        """Get the list of files that were uploaded."""
        return self._upload

    def get_download(self) -> List[Tuple[str, str]]:
        """Get the list of files that were downloaded."""
        return self._download
