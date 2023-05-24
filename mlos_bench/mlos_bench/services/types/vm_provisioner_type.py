#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Protocol interface for VM provisioning operations.
"""

from typing import Tuple, Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from mlos_bench.environments.status import Status


@runtime_checkable
class SupportsVMOps(Protocol):
    """
    Protocol interface for VM provisioning operations.
    """

    def vm_provision(self, config: dict, template: dict, params: dict) -> Tuple["Status", dict]:
        """
        Check if VM is ready. Deploy a new VM, if necessary.

        Parameters
        ----------
        config : dict
            Flat dictionary of (key, value) pairs of deployment configuration parameters.
        template : dict
            ARM Template with VM and other resources to deploy on Azure.
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

    def wait_vm_deployment(self, is_setup: bool, params: dict) -> Tuple["Status", dict]:
        """
        Waits for a pending operation on an Azure VM to resolve to SUCCEEDED or FAILED.
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

    def vm_start(self, vm_name: str, params: dict) -> Tuple["Status", dict]:
        """
        Start a VM.

        Parameters
        ----------
        vm_name : str
            Name of the VM to start.
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """

    def vm_stop(self, vm_name: str, params: dict) -> Tuple["Status", dict]:
        """
        Stops the VM by initiating a graceful shutdown.

        Parameters
        ----------
        vm_name : str
            Name of the VM to stop.
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """

    def vm_restart(self, vm_name: str, params: dict) -> Tuple["Status", dict]:
        """
        Restarts the VM by initiating a graceful shutdown.

        Parameters
        ----------
        vm_name : str
            Name of the VM to restart.
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """

    def vm_deprovision(self, params: dict) -> Tuple["Status", dict]:
        """
        Deallocate the resources deployed with `vm_provision` earlier.

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

    def wait_vm_operation(self, params: dict) -> Tuple["Status", dict]:
        """
        Waits for a pending operation on a VM to resolve to SUCCEEDED or FAILED.
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
