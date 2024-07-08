#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""OS-level remote Environment on Azure."""

import logging
from typing import Optional

from mlos_bench.environments.base_environment import Environment
from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.host_ops_type import SupportsHostOps
from mlos_bench.services.types.os_ops_type import SupportsOSOps
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class OSEnv(Environment):
    """OS Level Environment for a host."""

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
        Create a new environment for remote execution.

        Parameters
        ----------
        name: str
            Human-readable name of the environment.
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration. Each config must have at least the "tunable_params"
            and the "const_args" sections.
            `RemoteEnv` must also have at least some of the following parameters:
            {setup, run, teardown, wait_boot}
        global_config : dict
            Free-format dictionary of global parameters (e.g., security credentials)
            to be mixed in into the "const_args" section of the local config.
        tunables : TunableGroups
            A collection of tunable parameters for *all* environments.
        service: Service
            An optional service object (e.g., providing methods to
            deploy or reboot a VM, etc.).
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
            self._service, SupportsOSOps
        ), "RemoteEnv requires a service that supports host operations"
        self._os_service: SupportsOSOps = self._service

    def setup(self, tunables: TunableGroups, global_config: Optional[dict] = None) -> bool:
        """
        Check if the host is up and running; boot it, if necessary.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of groups of tunable parameters along with the
            parameters' values. HostEnv tunables are variable parameters that,
            together with the HostEnv configuration, are sufficient to provision
            and start a host.
        global_config : dict
            Free-format dictionary of global parameters of the environment
            that are not used in the optimization process.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("OS set up: %s :: %s", self, tunables)
        if not super().setup(tunables, global_config):
            return False

        (status, params) = self._host_service.start_host(self._params)
        if status.is_pending():
            (status, _) = self._host_service.wait_host_operation(params)

        # TODO: configure OS settings here?

        self._is_ready = status in {Status.SUCCEEDED, Status.READY}
        return self._is_ready

    def teardown(self) -> None:
        """Clean up and shut down the host without deprovisioning it."""
        _LOG.info("OS tear down: %s", self)
        (status, params) = self._os_service.shutdown(self._params)
        if status.is_pending():
            (status, _) = self._os_service.wait_os_operation(params)

        super().teardown()
        _LOG.debug("Final status of OS stopping: %s :: %s", self, status)
