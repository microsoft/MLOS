#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for managing hosts via SSH.
"""

from typing import Iterable, List, Optional, Tuple

import logging

import asyncssh

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.remote.ssh.ssh_service import SshService
from mlos_bench.services.types.remote_exec_type import SupportsRemoteExec
from mlos_bench.services.types.os_ops_type import SupportsOSOps
from mlos_bench.util import merge_parameters

_LOG = logging.getLogger(__name__)


class SshHostService(SshService, SupportsOSOps, SupportsRemoteExec):
    """
    Helper methods to manage machines via SSH.
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, config: dict, global_config: dict, parent: Optional[Service]):
        """
        Create a new instance of an SSH Service.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration.
        global_config : dict
            Free-format dictionary of global parameters.
        parent : Service
            Parent service that can provide mixin functions.
        """
        super().__init__(config, global_config, parent)

        # Register methods that we want to expose to the Environment objects.
        self.register([
            self.shutdown,
            self.reboot,
            self.wait_os_operation,
            self.remote_exec,
            self.get_remote_exec_results
        ])

    async def _run_cmd(self, conn: asyncssh.SSHClientConnection, cmd: str) -> asyncssh.SSHCompletedProcess:
        """
        Runs a command on a host via SSH.

        Parameters
        ----------
        conn : asyncssh.SSHClientConnection
            Connection to the host.
        cmd : str
            Command to run.

        Returns
        -------
        asyncssh.SSHCompletedProcess
            Returns the result of the command.
        """
        return await conn.run(cmd, check=True, timeout=self._request_timeout)

    def remote_exec(self, script: Iterable[str], config: dict,
                    env_params: dict) -> Tuple["Status", dict]:
        """
        Run a command on remote host OS.

        Parameters
        ----------
        script : Iterable[str]
            A list of lines to execute as a script on a remote VM.
        config : dict
            Flat dictionary of (key, value) pairs of parameters.
            They usually come from `const_args` and `tunable_params`
            properties of the Environment.
        env_params : dict
            Parameters to pass as *shell* environment variables into the script.
            This is usually a subset of `config` with some possible conversions.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        config = merge_parameters(
            dest=self.config.copy(),
            source=config,
            required_keys=[
                "ssh_hostname",
            ]
        )
        # TODO: port, username, key, etc. handling?


    def get_remote_exec_results(self, config: dict) -> Tuple["Status", dict]:
        """
        Get the results of the asynchronously running command.

        Parameters
        ----------
        config : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            Must have the "asyncResultsUrl" key to get the results.
            If the key is not present, return Status.PENDING.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
        """
        raise NotImplementedError("TODO")

    def _exec_os_op(self, cmd_opts_list: List[str], params: dict, force: bool = False) -> Tuple[Status, dict]:
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "ssh_hostname",
            ]
        )
        cmd_opts = ' '.join([f"'{cmd}'" for cmd in cmd_opts_list])
        script = r"if [[ $EUID -ne 0 ]]; then sudo=$(command -v sudo -n); sudo=${sudo:+$sudo -n}; fi; " \
            + f"for cmd in {cmd_opts}; do " \
            + r"  $sudo $cmd && exit 0;" \
            + r"done;" \
            + r"echo 'ERROR: Failed to shutdown system.'; exit 1"
        return self.remote_exec(script, config, env_params={})

    def shutdown(self, params: dict, force: bool = False) -> Tuple[Status, dict]:
        """
        Initiates a (graceful) shutdown of the Host/VM OS.

        Parameters
        ----------
        params: dict
            Flat dictionary of (key, value) pairs of tunable parameters.
        force : bool
            If True, force stop the Host/VM.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        cmd_opts_list = [
            'shutdown -h now',
            'poweroff',
            'halt -p',
            'systemctl poweroff',
        ]
        return self._exec_os_op(cmd_opts_list=cmd_opts_list, params=params, force=force)

    def reboot(self, params: dict, force: bool = False) -> Tuple[Status, dict]:
        """
        Initiates a (graceful) shutdown of the Host/VM OS.

        Parameters
        ----------
        params: dict
            Flat dictionary of (key, value) pairs of tunable parameters.
        force : bool
            If True, force restart the Host/VM.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        cmd_opts_list = [
            'shutdown -r now',
            'reboot',
            'halt --reboot',
            'systemctl reboot',
        ]
        return self._exec_os_op(cmd_opts_list=cmd_opts_list, params=params, force=force)

    def wait_os_operation(self, params: dict) -> Tuple[Status, dict]:
        """
        Waits for a pending operation on an OS to resolve to SUCCEEDED or FAILED.
        Return TIMED_OUT when timing out.

        Parameters
        ----------
        params: dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            Must have the "asyncResultsUrl" key to get the results.
            If the key is not present, return Status.PENDING.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
            Result is info on the operation runtime if SUCCEEDED, otherwise {}.
        """
        raise NotImplementedError("TODO")
