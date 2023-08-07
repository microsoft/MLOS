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
from typing import Any, Dict, Optional

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
    _TENTANT_ID = "72f988bf-86f1-41af-91ab-2d7cd011db47"

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 global_config: Optional[Dict[str, Any]] = None,
                 parent: Optional[Service] = None):
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
        """
        super().__init__(config, global_config, parent)

        # Register methods that we want to expose to the Environment objects.
        self.register([self.get_access_token])

        if "spClientId" in self.config:
            check_required_params(
                self.config, {
                    "keyVaultName",
                    "certName",
                    "spClientId",
                }
            )

        # This parameter can come from command line as strings, so conversion is needed.
        self._req_interval = float(self.config.get("tokenRequestInterval", self._REQ_INTERVAL))
        keyvault_name = self.config.get("keyVaultName")
        cert_name = self.config.get("certName")
        sp_client_id = self.config.get("spClientId")
        tenant_id = self.config.get("tenant", self._TENTANT_ID)

        self._access_token = "RENEW *NOW*"
        self._token_expiration_ts = datetime.datetime.now()  # Typically, some future timestamp.

        # Login as ourselves
        local_user_cred = azure_id.AzureCliCredential()
        self._cred = local_user_cred

        # Login as the Service Principal, if provided
        if sp_client_id is not None:
            assert keyvault_name is not None
            assert cert_name is not None

            # Get a client for fetching cert info
            keyvault_secrets_client = SecretClient(
                vault_url=f"https://{keyvault_name}.vault.azure.net",
                credential=local_user_cred,
            )

            # The certificate private key data is stored as hidden "Secret" (not Key strangely)
            #  in PKCS12 format, but we need to decode it.
            secret = keyvault_secrets_client.get_secret(cert_name)
            assert secret.value is not None
            cert_bytes = b64decode(secret.value)

            # Reauthenticate as the service principal.
            self._cred = azure_id.CertificateCredential(tenant_id=tenant_id, client_id=sp_client_id, certificate_data=cert_bytes)

    def get_access_token(self) -> str:
        """
        Get the access token from Azure CLI, if expired.
        """
        ts_diff = (self._token_expiration_ts - datetime.datetime.now()).total_seconds()
        _LOG.debug("Time to renew the token: %.2f sec.", ts_diff)
        if ts_diff < self._req_interval:
            _LOG.debug("Request new accessToken")
            res = self._cred.get_token("https://management.azure.com/.default")
            self._token_expiration_ts = datetime.datetime.fromtimestamp(res.expires_on)
            self._access_token = res.token
            _LOG.info("Got new accessToken. Expiration time: %s", self._token_expiration_ts)
        return self._access_token
