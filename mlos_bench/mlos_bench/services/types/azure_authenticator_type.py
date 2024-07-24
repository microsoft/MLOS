#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Protocol interface for authentication for the Azure services."""

from typing import Protocol, runtime_checkable
from mlos_bench.services.types.authenticator_type import SupportsAuth
import azure.core.credentials as azure_cred


@runtime_checkable
class SupportsAzureAuth(SupportsAuth, Protocol):
    """Protocol interface for authentication for the Azure services."""

    def get_credential(self) -> azure_cred.TokenCredential:
        """
        Get the credential object for Azure services.

        Returns
        -------
        credential : azure_cred.TokenCredential
            TokenCredential object.
        """
