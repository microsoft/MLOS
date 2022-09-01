"""
VM-level benchmark environment on Azure.
"""

import json
import logging

from mlos_bench.environment import Environment, Status

_LOG = logging.getLogger(__name__)


class VMEnv(Environment):
    """
    Azure VM environment.
    """

    def setup(self):
        """
        Check if the Azure VM can be provisioned.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("VM set up")
        return True

    def teardown(self):
        """
        Shut down the VM and release it.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("VM tear down")
        status, params = self._service.vm_deprovision()

        if status == Status.PENDING:
            try:
                status, _ = self._service.wait_vm_operation(params)
            except TimeoutError:
                _LOG.error("vm_deprovision timed out: %s", params)

        _LOG.debug("Final status of tear down: %s", status)

        return status == Status.READY

    def run(self, tunables):
        # pylint: disable=duplicate-code
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
        _LOG.info("Run: %s", tunables)
        params = self._combine_tunables(tunables)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Deploy VM:\n%s", json.dumps(params, indent=2))

        (status, _output) = self._service.vm_provision(params)
        return status in {Status.PENDING, Status.READY}
