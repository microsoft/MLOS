#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for mocking managing VMs.
"""

from typing import Any, Tuple

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.vm_provisioner_type import SupportsVMOps


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
            name: self._mock_operation for name in (
                "wait_vm_deployment",
                "wait_vm_operation",
                "vm_provision",
                "vm_start",
                "vm_stop",
                "vm_deprovision",
                "vm_restart",
            )
        })

    @staticmethod
    def _mock_operation(*args: Any, **kwargs: Any) -> Tuple[Status, dict]:
        """
        Mock VM operation that always succeeds.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result, always (SUCCEEDED, {}).
        """
        return Status.SUCCEEDED, {}
