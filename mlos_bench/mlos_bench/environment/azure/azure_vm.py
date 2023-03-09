"""
VM-level benchmark environment on Azure.
"""

import logging

from mlos_bench.environment import Environment
from mlos_bench.environment.tunable import TunableGroups

_LOG = logging.getLogger(__name__)


class VMEnv(Environment):
    """
    Azure VM environment.
    """

    def setup(self, tunables: TunableGroups) -> bool:
        """
        Check if Azure VM is ready. (Re)provision and start it, if necessary.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of groups of tunable parameters along with the
            parameters' values. VMEnv tunables are variable parameters that,
            together with the VMEnv configuration, are sufficient to provision
            and start a VM.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("VM set up: %s :: %s", self, tunables)
        if not super().setup(tunables):
            return False

        (status, params) = self._service.vm_provision(self._params)
        if status.is_pending:
            (status, _) = self._service.wait_vm_deployment(True, params)

        self._is_ready = status.is_succeeded
        return self._is_ready

    def teardown(self):
        """
        Shut down the VM and release it.
        """
        _LOG.info("VM tear down: %s", self)
        (status, params) = self._service.vm_deprovision()
        if status.is_pending:
            (status, _) = self._service.wait_vm_deployment(False, params)

        super().teardown()
        _LOG.debug("Final status of VM deprovisioning: %s :: %s", self, status)
