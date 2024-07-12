#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A collection Service functions for managing virtual networks on Azure."""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.remote.azure.azure_deployment_services import (
    AzureDeploymentService,
)
from mlos_bench.services.types.network_provisioner_type import (
    SupportsNetworkProvisioning,
)
from mlos_bench.util import merge_parameters

_LOG = logging.getLogger(__name__)


class AzureNetworkService(AzureDeploymentService, SupportsNetworkProvisioning):
    """Helper methods to manage Virtual Networks on Azure."""

    # Azure Compute REST API calls as described in
    # https://learn.microsoft.com/en-us/rest/api/virtualnetwork/virtual-networks?view=rest-virtualnetwork-2023-05-01

    # From: https://learn.microsoft.com/en-us/rest/api/virtualnetwork/virtual-networks?view=rest-virtualnetwork-2023-05-01  # pylint: disable=line-too-long # noqa
    _URL_DEPROVISION = (
        "https://management.azure.com"
        "/subscriptions/{subscription}"
        "/resourceGroups/{resource_group}"
        "/providers/Microsoft.Network"
        "/virtualNetwork/{vnet_name}"
        "/delete"
        "?api-version=2023-05-01"
    )

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        global_config: Optional[Dict[str, Any]] = None,
        parent: Optional[Service] = None,
        methods: Union[Dict[str, Callable], List[Callable], None] = None,
    ):
        """
        Create a new instance of Azure Network services proxy.

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
            self.merge_methods(
                methods,
                [
                    # SupportsNetworkProvisioning
                    self.provision_network,
                    self.deprovision_network,
                    self.wait_network_deployment,
                ],
            ),
        )
        if not self._deploy_template:
            raise ValueError(
                "AzureNetworkService requires a deployment template:\n"
                + f"config={config}\nglobal_config={global_config}"
            )

    def _set_default_params(self, params: dict) -> dict:  # pylint: disable=no-self-use
        # Try and provide a semi sane default for the deploymentName if not provided
        # since this is a common way to set the deploymentName and can same some
        # config work for the caller.
        if "vnetName" in params and "deploymentName" not in params:
            params["deploymentName"] = f"{params['vnetName']}-deployment"
            _LOG.info(
                "deploymentName missing from params. Defaulting to '%s'.",
                params["deploymentName"],
            )
        return params

    def wait_network_deployment(self, params: dict, *, is_setup: bool) -> Tuple[Status, dict]:
        """
        Waits for a pending operation on an Azure VM to resolve to SUCCEEDED or FAILED.
        Return TIMED_OUT when timing out.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
        is_setup : bool
            If True, wait for VM being deployed; otherwise, wait for successful deprovisioning.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
            Result is info on the operation runtime if SUCCEEDED, otherwise {}.
        """
        return self._wait_deployment(params, is_setup=is_setup)

    def provision_network(self, params: dict) -> Tuple[Status, dict]:
        """
        Deploy a virtual network, if necessary.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            NetworkEnv tunables are variable parameters that, together with the
            NetworkEnv configuration, are sufficient to provision a virtual network.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is the input `params` plus the
            parameters extracted from the response JSON, or {} if the status is FAILED.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        return self._provision_resource(params)

    def deprovision_network(self, params: dict, ignore_errors: bool = True) -> Tuple[Status, dict]:
        """
        Deprovisions the virtual network on Azure by deleting it.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
        ignore_errors : boolean
            Whether to ignore errors (default) encountered during the operation
            (e.g., due to dependent resources still in use).

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        params = self._set_default_params(params)
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "subscription",
                "resourceGroup",
                "deploymentName",
                "vnetName",
            ],
        )
        _LOG.info("Deprovision Network: %s", config["vnetName"])
        _LOG.info("Deprovision deployment: %s", config["deploymentName"])
        (status, results) = self._azure_rest_api_post_helper(
            config,
            self._URL_DEPROVISION.format(
                subscription=config["subscription"],
                resource_group=config["resourceGroup"],
                vnet_name=config["vnetName"],
            ),
        )
        if ignore_errors and status == Status.FAILED:
            _LOG.warning("Ignoring error: %s", results)
            status = Status.SUCCEEDED
        return (status, results)
