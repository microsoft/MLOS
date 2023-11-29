#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Network Environment.
"""

from typing import Optional

import logging

from mlos_bench.environments.base_environment import Environment
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.network_provisioner_type import SupportsNetworkProvisioning
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class NetworkEnv(Environment):
    """
    Network Environment.

    Used to model creating a virtual network (and network security group),
    but no real tuning is expected for it ... yet.
    """

    def __init__(self,
                 *,
                 name: str,
                 config: dict,
                 global_config: Optional[dict] = None,
                 tunables: Optional[TunableGroups] = None,
                 service: Optional[Service] = None):
        """
        Create a new environment for network operations.

        Parameters
        ----------
        name: str
            Human-readable name of the environment.
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration. Each config must have at least the "tunable_params"
            and the "const_args" sections.
        global_config : dict
            Free-format dictionary of global parameters (e.g., security credentials)
            to be mixed in into the "const_args" section of the local config.
        tunables : TunableGroups
            A collection of tunable parameters for *all* environments.
        service: Service
            An optional service object (e.g., providing methods to
            deploy a network, etc.).
        """
        super().__init__(name=name, config=config, global_config=global_config, tunables=tunables, service=service)

        # Virtual networks can be used for more than one experiment, so by default
        # we don't attempt to deprovision them.
        self._deprovision_on_teardown = config.get("deprovision_on_teardown", False)

        assert self._service is not None and isinstance(self._service, SupportsNetworkProvisioning), \
            "NetworkEnv requires a service that supports network provisioning"
        self._network_service: SupportsNetworkProvisioning = self._service

    def setup(self, tunables: TunableGroups, global_config: Optional[dict] = None) -> bool:
        """
        Check if network is ready. Provision, if necessary.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of groups of tunable parameters along with the
            parameters' values. NetworkEnv tunables are variable parameters that,
            together with the NetworkEnv configuration, are sufficient to provision
            and start a set of network resources (e.g., virtual network and network
            security group).
        global_config : dict
            Free-format dictionary of global parameters of the environment
            that are not used in the optimization process.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("Network set up: %s :: %s", self, tunables)
        if not super().setup(tunables, global_config):
            return False

        (status, params) = self._network_service.provision_network(self._params)
        if status.is_pending():
            (status, _) = self._network_service.wait_network_deployment(params, is_setup=True)

        self._is_ready = status.is_succeeded()
        return self._is_ready

    def teardown(self) -> None:
        """
        Shut down the Network and releases it.
        """
        if not self._deprovision_on_teardown:
            _LOG.info("Skipping Network deprovision: %s", self)
            return
        # Else
        _LOG.info("Network tear down: %s", self)
        (status, params) = self._network_service.deprovision_network(self._params, ignore_errors=True)
        if status.is_pending():
            (status, _) = self._network_service.wait_network_deployment(params, is_setup=False)

        super().teardown()
        _LOG.debug("Final status of Network deprovisioning: %s :: %s", self, status)
