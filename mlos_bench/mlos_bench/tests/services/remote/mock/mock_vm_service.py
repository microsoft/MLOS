#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A collection Service functions for mocking managing VMs."""

from collections.abc import Callable
from typing import Any

from mlos_bench.services.base_service import Service
from mlos_bench.services.types.host_ops_type import SupportsHostOps
from mlos_bench.services.types.host_provisioner_type import SupportsHostProvisioning
from mlos_bench.services.types.os_ops_type import SupportsOSOps
from mlos_bench.tests.services.remote.mock import mock_operation


class MockVMService(Service, SupportsHostProvisioning, SupportsHostOps, SupportsOSOps):
    """Mock VM service for testing."""

    # pylint: disable=too-many-ancestors

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        global_config: dict[str, Any] | None = None,
        parent: Service | None = None,
        methods: dict[str, Callable] | list[Callable] | None = None,
    ):
        """
        Create a new instance of mock VM services proxy.

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
                        # SupportsHostProvisioning:
                        "wait_host_deployment",
                        "provision_host",
                        "deprovision_host",
                        "deallocate_host",
                        # SupportsHostOps:
                        "start_host",
                        "stop_host",
                        "restart_host",
                        "wait_host_operation",
                        # SupportsOsOps:
                        "shutdown",
                        "reboot",
                        "wait_os_operation",
                    )
                },
            ),
        )
