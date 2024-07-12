#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Protocol interface for Host/VM boot operations."""

from typing import TYPE_CHECKING, Protocol, Tuple, runtime_checkable

if TYPE_CHECKING:
    from mlos_bench.environments.status import Status


@runtime_checkable
class SupportsHostOps(Protocol):
    """Protocol interface for Host/VM boot operations."""

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

    def stop_host(self, params: dict, force: bool = False) -> Tuple["Status", dict]:
        """
        Stops the Host/VM by initiating a (graceful) shutdown.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
        force : bool
            If True, force stop the Host/VM.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """

    def restart_host(self, params: dict, force: bool = False) -> Tuple["Status", dict]:
        """
        Restarts the host by initiating a (graceful) shutdown.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
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
