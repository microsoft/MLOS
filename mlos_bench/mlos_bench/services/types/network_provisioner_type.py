#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Protocol interface for Network provisioning operations."""

from typing import TYPE_CHECKING, Protocol, Tuple, runtime_checkable

if TYPE_CHECKING:
    from mlos_bench.environments.status import Status


@runtime_checkable
class SupportsNetworkProvisioning(Protocol):
    """Protocol interface for Network provisioning operations."""

    def provision_network(self, params: dict) -> Tuple["Status", dict]:
        """
        Check if Network is ready. Deploy a new Network, if necessary.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            NetworkEnv tunables are variable parameters that, together with the
            NetworkEnv configuration, are sufficient to provision a NetworkEnv.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """

    def wait_network_deployment(self, params: dict, *, is_setup: bool) -> Tuple["Status", dict]:
        """
        Waits for a pending operation on a Network to resolve to SUCCEEDED or FAILED.
        Return TIMED_OUT when timing out.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
        is_setup : bool
            If True, wait for Network being deployed; otherwise, wait for successful
            deprovisioning.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
            Result is info on the operation runtime if SUCCEEDED, otherwise {}.
        """

    def deprovision_network(
        self,
        params: dict,
        ignore_errors: bool = True,
    ) -> Tuple["Status", dict]:
        """
        Deprovisions the Network by deleting it.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
        ignore_errors : boolean
            Whether to ignore errors (default) encountered during the operation
            (e.g., due to dependent resources still in use).

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
