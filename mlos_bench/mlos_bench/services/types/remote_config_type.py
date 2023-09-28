#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Protocol interface for configuring cloud services.
"""

from typing import Protocol, Tuple, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from mlos_bench.environments.status import Status


@runtime_checkable
class SupportsRemoteConfig(Protocol):
    """
    Protocol interface for configuring cloud services.
    """

    # pylint: disable=too-few-public-methods

    def configure(self, config: dict) -> Tuple["Status", dict]:
        """
        Update configuration of the cloud service.

        Parameters
        ----------
        config : dict
            Flat dictionary of (key, value) pairs of tunable parameters.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
