#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Protocol interface for configuring cloud services."""

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from mlos_bench.environments.status import Status


@runtime_checkable
class SupportsRemoteConfig(Protocol):
    """Protocol interface for configuring cloud services."""

    def configure(self, config: dict[str, Any], params: dict[str, Any]) -> tuple["Status", dict]:
        """
        Update the parameters of a SaaS service in the cloud.

        Parameters
        ----------
        config : dict[str, Any]
            Key/value pairs of configuration parameters (e.g., vmName).
        params : dict[str, Any]
            Key/value pairs of the service parameters to update.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """

    def is_config_pending(self, config: dict[str, Any]) -> tuple["Status", dict]:
        """
        Check if the configuration of a service requires reboot or restart.

        Parameters
        ----------
        config : dict[str, Any]
            Key/value pairs of configuration parameters (e.g., vmName).

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result. A Boolean field
            "isConfigPendingRestart" indicates whether the service restart is required.
            If "isConfigPendingReboot" is set to True, rebooting a VM is necessary.
            Status is one of {PENDING, TIMED_OUT, SUCCEEDED, FAILED}
        """
