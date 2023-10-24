#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for mocking authentication.
"""

import logging
from typing import Any, Dict, Optional

from mlos_bench.services.base_service import Service
from mlos_bench.services.types.authenticator_type import SupportsAuth

_LOG = logging.getLogger(__name__)


class MockAuthService(Service, SupportsAuth):
    """
    A collection Service functions for mocking authentication ops.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None,
                 global_config: Optional[Dict[str, Any]] = None,
                 parent: Optional[Service] = None):
        # IMPORTANT: Save the local methods before invoking the base class constructor
        local_methods = [self.get_access_token]
        super().__init__(config, global_config, parent)
        self.register(local_methods)

    def get_access_token(self) -> str:
        return "TOKEN"
