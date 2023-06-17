#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Protocol interface for authentication for the cloud services.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class SupportsAuth(Protocol):
    """
    Protocol interface for authentication for the cloud services.
    """

    # pylint: disable=too-few-public-methods

    def get_access_token(self) -> str:
        """
        Get the access token for cloud services.

        Returns
        -------
        access_token : str
            Access token.
        """
