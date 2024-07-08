#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A collection Service functions for mocking authentication."""

import logging
from typing import Any, Callable, Dict, List, Optional, Union

from mlos_bench.services.base_service import Service
from mlos_bench.services.types.authenticator_type import SupportsAuth

_LOG = logging.getLogger(__name__)


class MockAuthService(Service, SupportsAuth):
    """A collection Service functions for mocking authentication ops."""

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
            self.merge_methods(
                methods,
                [
                    self.get_access_token,
                    self.get_auth_headers,
                ],
            ),
        )

    def get_access_token(self) -> str:
        return "TOKEN"

    def get_auth_headers(self) -> dict:
        return {"Authorization": "Bearer " + self.get_access_token()}
