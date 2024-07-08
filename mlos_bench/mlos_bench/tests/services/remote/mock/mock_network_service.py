#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A collection Service functions for mocking managing (Virtual) Networks."""

from typing import Any, Callable, Dict, List, Optional, Union

from mlos_bench.services.base_service import Service
from mlos_bench.services.types.network_provisioner_type import (
    SupportsNetworkProvisioning,
)
from mlos_bench.tests.services.remote.mock import mock_operation


class MockNetworkService(Service, SupportsNetworkProvisioning):
    """Mock Network service for testing."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        global_config: Optional[Dict[str, Any]] = None,
        parent: Optional[Service] = None,
        methods: Union[Dict[str, Callable], List[Callable], None] = None,
    ):
        """
        Create a new instance of mock network services proxy.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration.
        global_config : dict
            Free-format dictionary of global parameters.
        parent : Service
            Parent service that can provide mixin functions.
        """
        super().__init__(
            config,
            global_config,
            parent,
            self.merge_methods(
                methods,
                {
                    name: mock_operation
                    for name in (
                        # SupportsNetworkProvisioning:
                        "provision_network",
                        "deprovision_network",
                        "wait_network_deployment",
                    )
                },
            ),
        )
