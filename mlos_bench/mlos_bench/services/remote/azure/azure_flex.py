#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for managing VMs on Azure.
"""
import logging
from typing import Any, Dict, Optional, Tuple

import requests

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.authenticator_type import SupportsAuth
from mlos_bench.services.types.remote_config_type import SupportsRemoteConfig
from mlos_bench.util import check_required_params, merge_parameters

_LOG = logging.getLogger(__name__)


class AzureFlexConfigService(Service, SupportsRemoteConfig):
    """
    Helper methods to configure Azure Flex services.
    """

    _POLL_INTERVAL = 4     # seconds
    _POLL_TIMEOUT = 300    # seconds
    _REQUEST_TIMEOUT = 5   # seconds

    # Azure Flex Services Configuration REST API as described in
    # https://learn.microsoft.com/en-us/rest/api/mysql/flexibleserver/configurations

    _URL_CONFIGURE = (
        "https://management.azure.com" +
        "/subscriptions/{subscription}" +
        "/resourceGroups/{resource_group}" +
        "/providers/{provider}" +
        "/{server_type}/{vm_name}" +
        "/{update}" +
        "?api-version={api_version}"
    )

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 global_config: Optional[Dict[str, Any]] = None,
                 parent: Optional[Service] = None):
        """
        Create a new instance of Azure services proxy.

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

        check_required_params(self.config, {
            "subscription",
            "resourceGroup",
            "provider",
        })

        provider = self.config["provider"]
        if provider == "Microsoft.DBforMySQL":
            self._is_batch = True
            is_flex = True
            api_version = "2022-01-01"
        elif provider == "Microsoft.DBforMariaDB":
            self._is_batch = False
            is_flex = False
            api_version = "2018-06-01"
        elif provider == "Microsoft.DBforPostgreSQL":
            self._is_batch = False
            is_flex = True
            api_version = "2022-12-01"
        else:
            raise ValueError(f"Unsupported DB provider: {provider}")

        self._url_config = self._URL_CONFIGURE.format(
            subscription=self.config["subscription"],
            resource_group=self.config["resourceGroup"],
            provider=self.config["provider"],
            vm_name="{vm_name}",
            server_type="flexibleServers" if is_flex else "servers",
            update="updateConfigurations" if self._is_batch else "configurations/{param_name}",
            api_version=api_version,
        )

        # These parameters can come from command line as strings, so conversion is needed.
        self._poll_interval = float(self.config.get("pollInterval", self._POLL_INTERVAL))
        self._poll_timeout = float(self.config.get("pollTimeout", self._POLL_TIMEOUT))
        self._request_timeout = float(self.config.get("requestTimeout", self._REQUEST_TIMEOUT))

        self.register([self.configure])

    def configure(self, config: Dict[str, Any],
                  params: Dict[str, Any]) -> Tuple[Status, dict]:
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
        if self._is_batch:
            return self._config_batch(config, params)
        return self._config_many(config, params)

    def _get_headers(self) -> dict:
        """
        Get the headers for the REST API calls.
        """
        assert self._parent is not None and isinstance(self._parent, SupportsAuth), \
            "Authorization service not provided. Include service-auth.jsonc?"

        return {"Authorization": "Bearer " + self._parent.get_access_token()}

    def _config_one(self, config: Dict[str, Any],
                    param_name: str, param_value: Any) -> Tuple[Status, dict]:
        """
        Update a single parameter of the Azure DB service.

        Parameters
        ----------
        config : Dict[str, Any]
            Key/value pairs of configuration parameters (e.g., vmName).
        param_name : str
            Name of the parameter to update.
        param_value : Any
            Value of the parameter to update.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        config = merge_parameters(
            dest=self.config.copy(), source=config, required_keys=["vmName"])
        url = self._url_config.format(vm_name=config["vmName"], param_name=param_name)
        _LOG.debug("Request: PUT %s", url)
        response = requests.put(url, headers=self._get_headers(),
                                json={"properties": {"value": str(param_value)}},
                                timeout=self._request_timeout)
        _LOG.debug("Response: %s :: %s", response, response.text)
        return (Status.SUCCEEDED, {}) if response.status_code == 200 else (Status.FAILED, {})

    def _config_many(self, config: Dict[str, Any],
                     params: Dict[str, Any]) -> Tuple[Status, dict]:
        """
        Update the parameters of an Azure DB service one-by-one.
        (If batch API is not available for it).

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
        for (param_name, param_value) in params.items():
            (status, result) = self._config_one(config, param_name, param_value)
            if not status.is_succeeded():
                return (status, result)
        return (Status.SUCCEEDED, {})

    def _config_batch(self, config: Dict[str, Any],
                      params: Dict[str, Any]) -> Tuple[Status, dict]:
        """
        Batch update the parameters of an Azure DB service.

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
        config = merge_parameters(
            dest=self.config.copy(), source=config, required_keys=["vmName"])
        url = self._url_config.format(vm_name=config["vmName"])
        json_req = {
            "value": [
                {"name": key, "properties": {"value": str(val)}}
                for (key, val) in params.items()
            ],
            # "resetAllToDefault": "True"
        }
        _LOG.debug("Request: PUT %s", url)
        response = requests.put(url, headers=self._get_headers(),
                                json=json_req, timeout=self._request_timeout)
        _LOG.debug("Response: %s :: %s", response, response.text)
        return (Status.SUCCEEDED, {}) if response.status_code == 200 else (Status.FAILED, {})
