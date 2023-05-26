#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
"Remote" VM Environment.
"""

from typing import Optional

import logging

from mlos_bench.environments.base_environment import Environment
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.vm_provisioner_type import SupportsVMOps
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class VMEnv(Environment):
    """
    "Remote" VM environment.
    """

    def __init__(self,
                 *,
                 name: str,
                 config: dict,
                 global_config: Optional[dict] = None,
                 tunables: Optional[TunableGroups] = None,
                 service: Optional[Service] = None):
        """
        Create a new environment for VM operations.

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
            deploy or reboot a VM, etc.).
        """
        super().__init__(name=name, config=config, global_config=global_config,
                         tunables=tunables, service=service)

        assert self._service is not None and isinstance(self._service, SupportsVMOps), \
            "VMEnv requires a service that supports VM operations"
        self._vm_service: SupportsVMOps = self._service

    def setup(self, tunables: TunableGroups, global_config: Optional[dict] = None) -> bool:
        """
        Check if VM is ready. (Re)provision and start it, if necessary.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of groups of tunable parameters along with the
            parameters' values. VMEnv tunables are variable parameters that,
            together with the VMEnv configuration, are sufficient to provision
            and start a VM.
        global_config : dict
            Free-format dictionary of global parameters of the environment
            that are not used in the optimization process.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("VM set up: %s :: %s", self, tunables)
        if not super().setup(tunables, global_config):
            return False

        (status, params) = self._vm_service.vm_provision(self._params)
        if status.is_pending:
            (status, _) = self._vm_service.wait_vm_deployment(True, params)

        self._is_ready = status.is_succeeded
        return self._is_ready

    def teardown(self) -> None:
        """
        Shut down the VM and release it.
        """
        _LOG.info("VM tear down: %s", self)
        (status, params) = self._vm_service.vm_deprovision()
        if status.is_pending:
            (status, _) = self._vm_service.wait_vm_deployment(False, params)

        super().teardown()
        _LOG.debug("Final status of VM deprovisioning: %s :: %s", self, status)
