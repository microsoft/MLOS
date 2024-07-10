#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A collection Service functions for configuring SaaS instances on Azure."""
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import requests

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.authenticator_type import SupportsAuth
from mlos_bench.services.types.remote_config_type import SupportsRemoteConfig
from mlos_bench.util import check_required_params, merge_parameters

_LOG = logging.getLogger(__name__)


class AzureSaaSConfigService(Service, SupportsRemoteConfig):
    """Helper methods to configure Azure Flex services."""

    _REQUEST_TIMEOUT = 5  # seconds

    # REST API for Azure SaaS DB Services configuration as described in:
    # https://learn.microsoft.com/en-us/rest/api/mysql/flexibleserver/configurations
    # https://learn.microsoft.com/en-us/rest/api/postgresql/flexibleserver/configurations
    # https://learn.microsoft.com/en-us/rest/api/mariadb/configurations

    _URL_CONFIGURE = (
        "https://management.azure.com"
        "/subscriptions/{subscription}"
        "/resourceGroups/{resource_group}"
        "/providers/{provider}"
        "/{server_type}/{vm_name}"
        "/{update}"
        "?api-version={api_version}"
    )

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        global_config: Optional[Dict[str, Any]] = None,
        parent: Optional[Service] = None,
        methods: Union[Dict[str, Callable], List[Callable], None] = None,
    ):
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
        methods : Union[Dict[str, Callable], List[Callable], None]
            New methods to register with the service.
        """
        super().__init__(
            config,
            global_config,
            parent,
            self.merge_methods(methods, [self.configure, self.is_config_pending]),
        )

        check_required_params(
            self.config,
            {
                "subscription",
                "resourceGroup",
                "provider",
            },
        )

        # Provide sane defaults for known DB providers.
        provider = self.config.get("provider")
        if provider == "Microsoft.DBforMySQL":
            self._is_batch = self.config.get("supportsBatchUpdate", True)
            is_flex = self.config.get("isFlex", True)
            api_version = self.config.get("apiVersion", "2022-01-01")
        elif provider == "Microsoft.DBforMariaDB":
            self._is_batch = self.config.get("supportsBatchUpdate", False)
            is_flex = self.config.get("isFlex", False)
            api_version = self.config.get("apiVersion", "2018-06-01")
        elif provider == "Microsoft.DBforPostgreSQL":
            self._is_batch = self.config.get("supportsBatchUpdate", False)
            is_flex = self.config.get("isFlex", True)
            api_version = self.config.get("apiVersion", "2022-12-01")
        else:
            self._is_batch = self.config["supportsBatchUpdate"]
            is_flex = self.config["isFlex"]
            api_version = self.config["apiVersion"]

        self._url_config_set = self._URL_CONFIGURE.format(
            subscription=self.config["subscription"],
            resource_group=self.config["resourceGroup"],
            provider=self.config["provider"],
            vm_name="{vm_name}",
            server_type="flexibleServers" if is_flex else "servers",
            update="updateConfigurations" if self._is_batch else "configurations/{param_name}",
            api_version=api_version,
        )

        self._url_config_get = self._URL_CONFIGURE.format(
            subscription=self.config["subscription"],
            resource_group=self.config["resourceGroup"],
            provider=self.config["provider"],
            vm_name="{vm_name}",
            server_type="flexibleServers" if is_flex else "servers",
            update="configurations",
            api_version=api_version,
        )

        # These parameters can come from command line as strings, so conversion is needed.
        self._request_timeout = float(self.config.get("requestTimeout", self._REQUEST_TIMEOUT))

    def configure(self, config: Dict[str, Any], params: Dict[str, Any]) -> Tuple[Status, dict]:
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

    def is_config_pending(self, config: Dict[str, Any]) -> Tuple[Status, dict]:
        """
        Check if the configuration of an Azure DB service requires a reboot or restart.

        Parameters
        ----------
        config : Dict[str, Any]
            Key/value pairs of configuration parameters (e.g., vmName).

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result. A Boolean field
            "isConfigPendingRestart" indicates whether the service restart is required.
            If "isConfigPendingReboot" is set to True, rebooting a VM is necessary.
            Status is one of {PENDING, TIMED_OUT, SUCCEEDED, FAILED}
        """
        config = merge_parameters(dest=self.config.copy(), source=config, required_keys=["vmName"])
        url = self._url_config_get.format(vm_name=config["vmName"])
        _LOG.debug("Request: GET %s", url)
        response = requests.put(url, headers=self._get_headers(), timeout=self._request_timeout)
        _LOG.debug("Response: %s :: %s", response, response.text)
        if response.status_code == 504:
            return (Status.TIMED_OUT, {})
        if response.status_code != 200:
            return (Status.FAILED, {})
        # Currently, Azure Flex servers require a VM reboot.
        return (
            Status.SUCCEEDED,
            {
                "isConfigPendingReboot": any(
                    {"False": False, "True": True}[val["properties"]["isConfigPendingRestart"]]
                    for val in response.json()["value"]
                )
            },
        )

    def _get_headers(self) -> dict:
        """Get the headers for the REST API calls."""
        assert self._parent is not None and isinstance(
            self._parent, SupportsAuth
        ), "Authorization service not provided. Include service-auth.jsonc?"
        return self._parent.get_auth_headers()

    def _config_one(
        self,
        config: Dict[str, Any],
        param_name: str,
        param_value: Any,
    ) -> Tuple[Status, dict]:
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
        config = merge_parameters(dest=self.config.copy(), source=config, required_keys=["vmName"])
        url = self._url_config_set.format(vm_name=config["vmName"], param_name=param_name)
        _LOG.debug("Request: PUT %s", url)
        response = requests.put(
            url,
            headers=self._get_headers(),
            json={"properties": {"value": str(param_value)}},
            timeout=self._request_timeout,
        )
        _LOG.debug("Response: %s :: %s", response, response.text)
        if response.status_code == 504:
            return (Status.TIMED_OUT, {})
        if response.status_code == 200:
            return (Status.SUCCEEDED, {})
        return (Status.FAILED, {})

    def _config_many(self, config: Dict[str, Any], params: Dict[str, Any]) -> Tuple[Status, dict]:
        """
        Update the parameters of an Azure DB service one-by-one. (If batch API is not
        available for it).

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
        for param_name, param_value in params.items():
            (status, result) = self._config_one(config, param_name, param_value)
            if not status.is_succeeded():
                return (status, result)
        return (Status.SUCCEEDED, {})

    def _config_batch(self, config: Dict[str, Any], params: Dict[str, Any]) -> Tuple[Status, dict]:
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
        config = merge_parameters(dest=self.config.copy(), source=config, required_keys=["vmName"])
        url = self._url_config_set.format(vm_name=config["vmName"])
        json_req = {
            "value": [
                {"name": key, "properties": {"value": str(val)}} for (key, val) in params.items()
            ],
            # "resetAllToDefault": "True"
        }
        _LOG.debug("Request: POST %s", url)
        response = requests.post(
            url,
            headers=self._get_headers(),
            json=json_req,
            timeout=self._request_timeout,
        )
        _LOG.debug("Response: %s :: %s", response, response.text)
        if response.status_code == 504:
            return (Status.TIMED_OUT, {})
        if response.status_code == 200:
            return (Status.SUCCEEDED, {})
        return (Status.FAILED, {})
