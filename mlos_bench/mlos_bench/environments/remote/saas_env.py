#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Cloud-based (configurable) SaaS environment."""

import logging
from typing import Optional

from mlos_bench.environments.base_environment import Environment
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.host_ops_type import SupportsHostOps
from mlos_bench.services.types.remote_config_type import SupportsRemoteConfig
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class SaaSEnv(Environment):
    """Cloud-based (configurable) SaaS environment."""

    def __init__(
        self,
        *,
        name: str,
        config: dict,
        global_config: Optional[dict] = None,
        tunables: Optional[TunableGroups] = None,
        service: Optional[Service] = None,
    ):
        """
        Create a new environment for (configurable) cloud-based SaaS instance.

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
            An optional service object
            (e.g., providing methods to configure the remote service).
        """
        super().__init__(
            name=name,
            config=config,
            global_config=global_config,
            tunables=tunables,
            service=service,
        )

        assert self._service is not None and isinstance(
            self._service, SupportsHostOps
        ), "RemoteEnv requires a service that supports host operations"
        self._host_service: SupportsHostOps = self._service

        assert self._service is not None and isinstance(
            self._service, SupportsRemoteConfig
        ), "SaaSEnv requires a service that supports remote host configuration API"
        self._config_service: SupportsRemoteConfig = self._service

    def setup(self, tunables: TunableGroups, global_config: Optional[dict] = None) -> bool:
        """
        Update the configuration of a remote SaaS instance.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of groups of tunable parameters along with the
            parameters' values.
        global_config : dict
            Free-format dictionary of global parameters of the environment
            that are not used in the optimization process.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("SaaS set up: %s :: %s", self, tunables)
        if not super().setup(tunables, global_config):
            return False

        (status, _) = self._config_service.configure(
            self._params,
            self._tunable_params.get_param_values(),
        )
        if not status.is_succeeded():
            return False

        (status, res) = self._config_service.is_config_pending(self._params)
        if not status.is_succeeded():
            return False

        # Azure Flex DB instances currently require a VM reboot after reconfiguration.
        if res.get("isConfigPendingRestart") or res.get("isConfigPendingReboot"):
            _LOG.info("Restarting: %s", self)
            (status, params) = self._host_service.restart_host(self._params)
            if status.is_pending():
                (status, _) = self._host_service.wait_host_operation(params)
            if not status.is_succeeded():
                return False

            _LOG.info("Wait to restart: %s", self)
            (status, params) = self._host_service.start_host(self._params)
            if status.is_pending():
                (status, _) = self._host_service.wait_host_operation(params)

        self._is_ready = status.is_succeeded()
        return self._is_ready
