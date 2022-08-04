"OS-level benchmark environment on Azure."

import json
import logging

from mlos_bench.environment import Environment, Status

_LOG = logging.getLogger(__name__)


class OSEnv(Environment):
    "Boot-time environment for Azure VM."

    def setup(self):
        """
        Check if the Azure VM is provisioned and can be booted.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("Set up")
        return True

    def teardown(self):
        """
        Clean up and shut down the VM without deprovisioning it.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("Tear down")
        return True

    def run(self, tunables):
        """
        Check if Azure VM is up and running. (Re)boot it, if necessary.

        Parameters
        ----------
        tunables : dict
            Flat dictionary of (key, value) of the OS boot-time parameters.

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
