"""
OS-level benchmark environment on Azure.
"""

import json
import logging

from mlos_bench.environment import Environment, Status

_LOG = logging.getLogger(__name__)


class OSEnv(Environment):
    """
    Boot-time environment for Azure VM.
    """

    def setup(self):
        """
        Check if the Azure VM is up and running; boot it, if necessary.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("OS set up")
        return True

    def teardown(self):
        """
        Clean up and shut down the VM without deprovisioning it.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("OS tear down")
        status, params = self._service.vm_stop()

        if status == Status.PENDING:
            try:
                status, _ = self._service.wait_vm_operation(params)
            except TimeoutError:
                _LOG.error("vm_stop timed out: %s", params)

        _LOG.debug("Final status of tear down: %s", status)

        return status == Status.READY

    def run(self, tunables):
        # pylint: disable=duplicate-code
        """
        Check if Azure VM is up and running. (Re)boot it, if necessary.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of groups of tunable parameters
            along with the parameters' values.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("Run: %s", tunables)
        params = self._combine_tunables(tunables)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Start VM:\n%s", json.dumps(params, indent=2))

        # TODO: Reboot the OS when config parameters change
        (status, _output) = self._service.vm_start(params)
        return status in {Status.PENDING, Status.READY}
