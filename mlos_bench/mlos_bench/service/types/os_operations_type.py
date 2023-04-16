#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Protocol interface for OS operations.
"""

from typing import Tuple, Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from mlos_bench.environment.status import Status


@runtime_checkable
class SupportsOSOps(Protocol):
    # pylint: disable=too-few-public-methods
    """
    Protocol interface for OS operations.
    """

    def os_reboot(self) -> Tuple["Status", dict]:
        """
        Reboot the OS by initiating a graceful shutdown.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
