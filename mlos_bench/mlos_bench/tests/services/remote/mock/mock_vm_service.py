#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for mocking managing VMs.
"""

import logging

from typing import Tuple

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.vm_provisioner_type import SupportsVMOps
from mlos_bench.util import check_required_params

_LOG = logging.getLogger(__name__)


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

        check_required_params(
            config, {
                "vmName",
            }
        )

        # Register methods that we want to expose to the Environment objects.
        self.register([
            self.wait_vm_deployment,
            self.wait_vm_operation,
            self.vm_provision,
            self.vm_start,
            self.vm_stop,
            self.vm_deprovision,
            self.vm_restart,
        ])

    def wait_vm_deployment(self, is_setup: bool, params: dict) -> Tuple[Status, dict]:
        """
        Waits for a pending operation on an mock VM to resolve to SUCCEEDED or FAILED.
        Return TIMED_OUT when timing out.

        Parameters
        ----------
        is_setup : bool
            If True, wait for VM being deployed; otherwise, wait for successful deprovisioning.
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
            Result is info on the operation runtime if SUCCEEDED, otherwise {}.
        """
        return Status.SUCCEEDED, {}

    def wait_vm_operation(self, params: dict) -> Tuple[Status, dict]:
        """
        Waits for a pending operation on an mock VM to resolve to SUCCEEDED or FAILED.
        Return TIMED_OUT when timing out.

        Parameters
        ----------
        params: dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            Must have the "asyncResultsUrl" key to get the results.
            If the key is not present, return Status.PENDING.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
            Result is info on the operation runtime if SUCCEEDED, otherwise {}.
        """
        return Status.SUCCEEDED, {}

    def vm_provision(self, params: dict) -> Tuple[Status, dict]:
        """
        Check if mock VM is ready. Deploy a new VM, if necessary.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            VMEnv tunables are variable parameters that, together with the
            VMEnv configuration, are sufficient to provision a VM.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        return Status.SUCCEEDED, {}

    def vm_start(self, params: dict) -> Tuple[Status, dict]:
        """
        Start the mock VM.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        return Status.SUCCEEDED, {}

    def vm_stop(self) -> Tuple[Status, dict]:
        """
        Stops the mock VM by initiating a graceful shutdown.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        return Status.SUCCEEDED, {}

    def vm_deprovision(self) -> Tuple[Status, dict]:
        """
        Deallocates the mock VM by shutting it down then releasing the compute resources.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        return Status.SUCCEEDED, {}

    def vm_restart(self) -> Tuple[Status, dict]:
        """
        Reboot the mock VM by initiating a graceful shutdown.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        return Status.SUCCEEDED, {}
