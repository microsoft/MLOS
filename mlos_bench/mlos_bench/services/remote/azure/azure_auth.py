#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for managing VMs on Azure.
"""

import datetime
import json
import logging
import subprocess

from mlos_bench.services.base_service import Service
from mlos_bench.services.types.authenticator_type import SupportsAuth

_LOG = logging.getLogger(__name__)


class AzureAuthService(Service, SupportsAuth):
    """
    Helper methods to get access to Azure services.
    """

    _REQ_INTERVAL = 300   # = 5 min

    def __init__(self, config: dict, parent: Service):
        """
        Create a new instance of Azure authentication services proxy.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration.
        parent : Service
            Parent service that can provide mixin functions.
        """
        super().__init__(config, parent)

        # Register methods that we want to expose to the Environment objects.
        self.register([self.get_access_token])

        # This parameter can come from command line as strings, so conversion is needed.
        self._req_interval = float(config.get("tokenRequestInterval", self._REQ_INTERVAL))

        self._access_token = "RENEW *NOW*"
        self._token_expiration_ts = datetime.datetime.now()  # Typically, some future timestamp.

    def get_access_token(self) -> str:
        """
        Get the access token from Azure CLI, if expired.
        """
        ts_diff = (self._token_expiration_ts - datetime.datetime.now()).seconds
        _LOG.debug("Time to renew the token: %d sec.", ts_diff)
        if ts_diff < self._req_interval:
            _LOG.debug("Request new accessToken")
            res = json.loads(subprocess.check_output(
                'az account get-access-token', shell=True, text=True))
            self._token_expiration_ts = datetime.datetime.fromisoformat(res["expiresOn"])
            self._access_token = res["accessToken"]
            _LOG.info("Got new accessToken. Expiration time: %s", self._token_expiration_ts)
        return self._access_token
