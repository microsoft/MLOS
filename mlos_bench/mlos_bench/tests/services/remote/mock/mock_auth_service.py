#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A collection Service functions for mocking authentication."""

import logging
from typing import Any, Dict, List, Optional, Union
from collections.abc import Callable

from mlos_bench.services.base_service import Service
from mlos_bench.services.types.authenticator_type import SupportsAuth

_LOG = logging.getLogger(__name__)


class MockAuthService(Service, SupportsAuth[str]):
    """A collection Service functions for mocking authentication ops."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        global_config: dict[str, Any] | None = None,
        parent: Service | None = None,
        methods: dict[str, Callable] | list[Callable] | None = None,
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
                    self.get_credential,
                ],
            ),
        )

    def get_access_token(self) -> str:
        return "TOKEN"

    def get_auth_headers(self) -> dict:
        return {"Authorization": "Bearer " + self.get_access_token()}

    def get_credential(self) -> str:
        return "MOCK CREDENTIAL"
