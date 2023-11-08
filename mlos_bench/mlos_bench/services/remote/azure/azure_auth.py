#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for managing VMs on Azure.
"""

import datetime
import logging
from base64 import b64decode
from typing import Any, Callable, Dict, List, Optional, Union

import azure.identity as azure_id
from azure.keyvault.secrets import SecretClient

from mlos_bench.services.base_service import Service
from mlos_bench.services.types.authenticator_type import SupportsAuth
from mlos_bench.util import check_required_params

_LOG = logging.getLogger(__name__)


class AzureAuthService(Service, SupportsAuth):
    """
    Helper methods to get access to Azure services.
    """

    _REQ_INTERVAL = 300   # = 5 min

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 global_config: Optional[Dict[str, Any]] = None,
                 parent: Optional[Service] = None,
                 methods: Union[Dict[str, Callable], List[Callable], None] = None):
        """
        Create a new instance of Azure authentication services proxy.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration.
        global_config : dict
            Free-format dictionary of global parameters.
        parent : Service
            Parent service that can provide mixin functions.
        methods : Union[Dict[str, Callable], List[Callable], None]
            New methods to register with the service.
        """
        super().__init__(
            config, global_config, parent,
            self.merge_methods(methods, [
                self.get_access_token,
                self.get_auth_headers,
            ])
        )

        # This parameter can come from command line as strings, so conversion is needed.
        self._req_interval = float(self.config.get("tokenRequestInterval", self._REQ_INTERVAL))

        self._access_token = "RENEW *NOW*"
        self._token_expiration_ts = datetime.datetime.utcnow()  # Typically, some future timestamp.

        # Login as ourselves
        self._cred: Union[azure_id.AzureCliCredential, azure_id.CertificateCredential]
        self._cred = azure_id.AzureCliCredential()

        # Verify info required for SP auth early
        if "spClientId" in self.config:
            check_required_params(
                self.config, {
                    "spClientId",
                    "keyVaultName",
                    "certName",
                    "tenant",
                }
            )

    def _init_sp(self) -> None:
        # Perform this initialization outside of __init__ so that environment loading tests
        # don't need to specifically mock keyvault interactions out

        # Already logged in as SP
        if isinstance(self._cred, azure_id.CertificateCredential):
            return

        sp_client_id = self.config["spClientId"]
        keyvault_name = self.config["keyVaultName"]
        cert_name = self.config["certName"]
        tenant_id = self.config["tenant"]

        # Get a client for fetching cert info
        keyvault_secrets_client = SecretClient(
            vault_url=f"https://{keyvault_name}.vault.azure.net",
            credential=self._cred,
        )

        # The certificate private key data is stored as hidden "Secret" (not Key strangely)
        # in PKCS12 format, but we need to decode it.
        secret = keyvault_secrets_client.get_secret(cert_name)
        assert secret.value is not None
        cert_bytes = b64decode(secret.value)

        # Reauthenticate as the service principal.
        self._cred = azure_id.CertificateCredential(tenant_id=tenant_id, client_id=sp_client_id, certificate_data=cert_bytes)

    def get_access_token(self) -> str:
        """
        Get the access token from Azure CLI, if expired.
        """
        # Ensure we are logged as the Service Principal, if provided
        if "spClientId" in self.config:
            self._init_sp()

        ts_diff = (self._token_expiration_ts - datetime.datetime.utcnow()).total_seconds()
        _LOG.debug("Time to renew the token: %.2f sec.", ts_diff)
        if ts_diff < self._req_interval:
            _LOG.debug("Request new accessToken")
            res = self._cred.get_token("https://management.azure.com/.default")
            self._token_expiration_ts = datetime.datetime.utcfromtimestamp(res.expires_on)
            self._access_token = res.token
            _LOG.info("Got new accessToken. Expiration time: %s", self._token_expiration_ts)
        return self._access_token

    def get_auth_headers(self) -> dict:
        """
        Get the authorization part of HTTP headers for REST API calls.
        """
        return {"Authorization": "Bearer " + self.get_access_token()}
