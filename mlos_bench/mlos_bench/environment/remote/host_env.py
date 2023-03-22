#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Remote host Environment.
"""

import logging

from mlos_bench.environment import Environment
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class HostEnv(Environment):
    """
    Remote host environment.
    """

    def setup(self, tunables: TunableGroups, global_config: dict = None) -> bool:
        """
        Check if the host is ready. (Re)provision and start it, if necessary.

        For VM hosts, this will involve creating the VM (if necessary) using
        its Service provider mix-in and ensuring its powered on.

        Note: for physical hosts very often this will be a no-op and expected
        to be a manual operation for physical hosts.

        However, there are some environments (e.g. CloudLab or Redfish firmware
        configuration) where the host can be provisioned, configured, and
        started programmatically.  This is a good place to hook into such
        environments.


        Parameters
        ----------
        tunables : TunableGroups
            A collection of groups of tunable parameters along with the
            parameters' values. HostEnv tunables are variable parameters that,
            together with the HostEnv configuration, are sufficient to provision
            and start a Host.
        global_config : dict
            Free-format dictionary of global parameters of the environment
            that are not used in the optimization process.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("Host set up: %s :: %s", self, tunables)
        if not super().setup(tunables, global_config):
            return False

        (status, params) = self._service.host_provision(self._params)
        if status.is_pending:
            (status, _) = self._service.wait_host_deployment(True, params)

        self._is_ready = status.is_succeeded
        return self._is_ready

    def teardown(self):
        """
        Shut down the Host and release it.
        """
        _LOG.info("Host tear down: %s", self)
        (status, params) = self._service.host_deprovision()
        if status.is_pending:
            (status, _) = self._service.wait_host_deployment(False, params)

        super().teardown()
        _LOG.debug("Final status of Host deprovisioning: %s :: %s", self, status)
