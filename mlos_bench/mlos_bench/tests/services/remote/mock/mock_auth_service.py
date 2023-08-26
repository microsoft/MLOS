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
        super().__init__(config, global_config, parent)

        self.register([
            self.get_access_token
        ])

    def get_access_token(self) -> str:
        return "TOKEN"
