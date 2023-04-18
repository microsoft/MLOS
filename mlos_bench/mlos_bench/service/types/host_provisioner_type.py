#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Protocol interface for Host/VM provisioning operations.
"""

from typing import Tuple, Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from mlos_bench.environment.status import Status


@runtime_checkable
class SupportsHostOps(Protocol):
    """
    Protocol interface for Host/VM provisioning operations.
    """

    def provision_host(self, params: dict) -> Tuple["Status", dict]:
        """
        Check if Host/VM is ready. Deploy a new Host/VM, if necessary.

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

    def wait_host_deployment(self, is_setup: bool, params: dict) -> Tuple["Status", dict]:
        """
        Waits for a pending operation on a Host/VM to resolve to SUCCEEDED or FAILED.
        Return TIMED_OUT when timing out.

        Parameters
        ----------
        is_setup : bool
            If True, wait for Host/VM being deployed; otherwise, wait for successful deprovisioning.
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
            Result is info on the operation runtime if SUCCEEDED, otherwise {}.
        """

    def deprovision_host(self) -> Tuple["Status", dict]:
        """
        Deallocates the Host/VM by shutting it down then releasing the compute resources.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """

    def start_host(self, params: dict) -> Tuple["Status", dict]:
        """
        Start a Host/VM.

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

    def stop_host(self, force: bool = False) -> Tuple["Status", dict]:
        """
        Stops the Host/VM by initiating a (graceful) shutdown.

        Parameters
        ----------
        force : bool
            If True, force stop the Host/VM.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """

    def restart_host(self, force: bool = False) -> Tuple["Status", dict]:
        """
        Restarts the host by initiating a (graceful) shutdown.

        Parameters
        ----------
        force : bool
            If True, force restart the Host/VM.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """

    def wait_host_operation(self, params: dict) -> Tuple["Status", dict]:
        """
        Waits for a pending operation on a Host/VM to resolve to SUCCEEDED or FAILED.
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
