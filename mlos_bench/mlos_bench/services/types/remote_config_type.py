#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Protocol interface for configuring cloud services.
"""

from typing import Any, Dict, Protocol, Tuple, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from mlos_bench.environments.status import Status


@runtime_checkable
class SupportsRemoteConfig(Protocol):
    """
    Protocol interface for configuring cloud services.
    """

    # pylint: disable=too-few-public-methods

    def configure(self, config: Dict[str, Any],
                  params: Dict[str, Any]) -> Tuple["Status", dict]:
        """
        Update the parameters of an Azure DB service.

        Parameters
        ----------
        config : Dict[str, Any]
            Key/value pairs of configuration parameters (e.g., vmName).
        params : Dict[str, Any]
            Key/value pairs of the service parameters to update.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
