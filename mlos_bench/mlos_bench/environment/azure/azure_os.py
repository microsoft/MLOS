"""
OS-level benchmark environment on Azure.
"""

import json
import logging
from typing import Optional

from mlos_bench.environment import Environment, Status, _check_required_params
from mlos_bench.environment.base_service import Service
from mlos_bench.environment.tunable import TunableGroups

_LOG = logging.getLogger(__name__)


class OSEnv(Environment):
    """
    Boot-time environment for Azure VM.
    """

    def __init__(self,
        name: str,
        config: dict,
        global_config: dict,
        tunables: TunableGroups,
        service: Optional[Service] = None,
    ):
        # pylint: disable=too-many-arguments
        """
        Create a new OS environment with a given config.

        Parameters
        ----------
        name: str
            Human-readable name of the environment.
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration. Each config must have at least the "tunable_params"
            and the "const_args" sections; the "cost" field can be omitted
            and is 0 by default.
        global_config : dict
            Free-format dictionary of global parameters (e.g., security credentials)
            to be mixed in into the "const_args" section of the local config.
        tunables : TunableGroups
            A collection of tunable parameters for *all* environments.
        service: Service
            An optional service object (e.g., providing methods to
            deploy or reboot a VM, etc.).
        """
        super().__init__(name, config, global_config, tunables, service)

        _check_required_params(config, [
            "fileShareMountScriptPath",
        ])
        self._fs_mnt_script_path = self.config.get("fileShareMountScriptPath")

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

        # Cleanup for the workload
        status, cmd_output = self._service.remote_exec(["/mnt/osat-fs/cleanup-workload.sh"], {})
        # Wait for cleanup script to complete
        if status == Status.PENDING:
            try:
                status, _cleanup_output = self._service.get_remote_exec_results(cmd_output)
            except TimeoutError:
                _LOG.error("Cleanup workload timed out: %s", cmd_output)
                return False
        if status != Status.READY:
            return False

        # Stop VM
        status, params = self._service.vm_stop()
        # Wait for VM stop to complete
        if status == Status.PENDING:
            try:
                status, _ = self._service.wait_vm_operation(params)
            except TimeoutError:
                _LOG.error("vm_stop timed out: %s", params)
                return False

        _LOG.info("Final status of OS tear down: %s", status)

        return status == Status.READY

    def run(self, tunables: TunableGroups):
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
        # Wait for VM start to complete
        if status == Status.PENDING:
            try:
                status, _ = self._service.wait_vm_operation(_output)
            except TimeoutError:
                _LOG.error("vm_start timed out: %s", _output)
                return False
        if status != Status.READY:
            return False

        # Ensure fileshare is mounted on VM
        with open(self._fs_mnt_script_path, mode="r", encoding="utf-8") as script:
            cmd_lines = script.readlines()
        status, cmd_output = self._service.remote_exec(cmd_lines, params)
        # Wait for mounting to complete
        if status == Status.PENDING:
            try:
                status, _mount_output = self._service.get_remote_exec_results(cmd_output)
                _LOG.debug("Mount file share: %s", _mount_output)
            except TimeoutError:
                _LOG.error("Mounting file share timed out: %s", cmd_output)
                return False
        if status != Status.READY:
            return False

        # Setup workload
        status, cmd_output = self._service.remote_exec(["/mnt/osat-fs/setup-workload.sh"], {})
        # Wait for setup script to complete
        if status == Status.PENDING:
            try:
                status, _setup_output = self._service.get_remote_exec_results(cmd_output)
                _LOG.debug("Setup workload: %s", _setup_output)
            except TimeoutError:
                _LOG.error("Setup workload timed out: %s", cmd_output)
                return False

        return status in {Status.PENDING, Status.READY}
