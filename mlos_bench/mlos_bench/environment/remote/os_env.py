"""
OS-level remote Environment on Azure.
"""

import logging

from mlos_bench.environment import Environment, Status
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class OSEnv(Environment):
    """
    OS Level Environment for a host.
    """

    def setup(self, tunables: TunableGroups, global_config: dict = None) -> bool:
        """
        Check if the host is up and running; boot it, if necessary.

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
        _LOG.info("OS set up: %s :: %s", self, tunables)
        if not super().setup(tunables, global_config):
            return False

        (status, params) = self._service.vm_start(self._params)
        if status.is_pending:
            (status, _) = self._service.wait_vm_operation(params)

        self._is_ready = status in {Status.SUCCEEDED, Status.READY}
        return self._is_ready

    def teardown(self):
        """
        Clean up and shut down the host without deprovisioning it.
        """
        _LOG.info("OS tear down: %s", self)
        (status, params) = self._service.vm_stop()
        if status.is_pending:
            (status, _) = self._service.wait_vm_operation(params)

        super().teardown()
        _LOG.debug("Final status of OS stopping: %s :: %s", self, status)
