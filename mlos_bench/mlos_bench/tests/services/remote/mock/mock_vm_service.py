#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for mocking managing VMs.
"""

from mlos_bench.services.base_service import Service
from mlos_bench.services.types.vm_provisioner_type import SupportsVMOps
from mlos_bench.tests.services.remote.mock import mock_operation


class MockVMService(Service, SupportsVMOps):
    """
    Mock VM service for testing.
    """

    def __init__(self, config: dict, parent: Service):
        """
        Create a new instance of mock VM services proxy.

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
            name: mock_operation for name in (
                "wait_vm_deployment",
                "wait_vm_operation",
                "vm_provision",
                "vm_start",
                "vm_stop",
                "vm_deprovision",
                "vm_restart",
            )
        })
