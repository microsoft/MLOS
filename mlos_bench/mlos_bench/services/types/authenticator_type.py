#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Protocol interface for authentication for the cloud services."""

from typing import Protocol, TypeVar, runtime_checkable

T_co = TypeVar("T_co", covariant=True)
"""Type variable for the return type of the credential object."""


@runtime_checkable
class SupportsAuth(Protocol[T_co]):
    """Protocol interface for authentication for the cloud services."""

    def get_access_token(self) -> str:
        """
        Get the access token for cloud services.

        Returns
        -------
        access_token : str
            Access token.
        """

    def get_auth_headers(self) -> dict:
        """
        Get the authorization part of HTTP headers for REST API calls.

        Returns
        -------
        access_header : dict
            HTTP header containing the access token.
        """

    def get_credential(self) -> T_co:
        """
        Get the credential object for cloud services.

        Returns
        -------
        credential : T_co
            Cloud-specific credential object.
        """
