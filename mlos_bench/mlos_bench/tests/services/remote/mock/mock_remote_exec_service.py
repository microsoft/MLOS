#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for mocking remote script execution.
"""

from mlos_bench.services.base_service import Service
from mlos_bench.services.types.remote_exec_type import SupportsRemoteExec
from mlos_bench.tests.services.remote.mock import mock_operation


class MockRemoteExecService(Service, SupportsRemoteExec):
    """
    Mock remote script execution service.
    """

    def __init__(self, config: dict, parent: Service):
        """
        Create a new instance of mock remote exec service.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration.
        parent : Service
            Parent service that can provide mixin functions.
        """
        super().__init__(config, parent)
        self.register({
            "remote_exec": mock_operation,
            "get_remote_exec_results": mock_operation,
        })
