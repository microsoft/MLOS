#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A collection Service functions for managing hosts via SSH."""

import logging
from concurrent.futures import Future
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

from asyncssh import ConnectionLost, DisconnectError, ProcessError, SSHCompletedProcess

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.remote.ssh.ssh_service import SshService
from mlos_bench.services.types.os_ops_type import SupportsOSOps
from mlos_bench.services.types.remote_exec_type import SupportsRemoteExec
from mlos_bench.util import merge_parameters

_LOG = logging.getLogger(__name__)


class SshHostService(SshService, SupportsOSOps, SupportsRemoteExec):
    """Helper methods to manage machines via SSH."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        global_config: Optional[Dict[str, Any]] = None,
        parent: Optional[Service] = None,
        methods: Union[Dict[str, Callable], List[Callable], None] = None,
    ):
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
        methods : Union[Dict[str, Callable], List[Callable], None]
            New methods to register with the service.
        """
        # Same methods are also provided by the AzureVMService class
        # pylint: disable=duplicate-code
        super().__init__(
            config,
            global_config,
            parent,
            self.merge_methods(
                methods,
                [
                    self.shutdown,
                    self.reboot,
                    self.wait_os_operation,
                    self.remote_exec,
                    self.get_remote_exec_results,
                ],
            ),
        )
        self._shell = self.config.get("ssh_shell", "/bin/bash")

    async def _run_cmd(
        self,
        params: dict,
        script: Iterable[str],
        env_params: dict,
    ) -> SSHCompletedProcess:
        """
        Runs a command asynchronously on a host via SSH.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of parameters (used for
            establishing the connection).
        cmd : str
            Command(s) to run via shell.

        Returns
        -------
        SSHCompletedProcess
            Returns the result of the command.
        """
        if isinstance(script, str):
            # Script should be an iterable of lines, not an iterable string.
            script = [script]
        connection, _ = await self._get_client_connection(params)
        # Note: passing environment variables to SSH servers is typically restricted
        # to just some LC_* values.
        # Handle transferring environment variables by making a script to set them.
        env_script_lines = [f"export {name}='{value}'" for (name, value) in env_params.items()]
        script_lines = env_script_lines + [
            line_split for line in script for line_split in line.splitlines()
        ]
        # Note: connection.run() uses "exec" with a shell by default.
        script_str = "\n".join(script_lines)
        _LOG.debug("Running script on %s:\n%s", connection, script_str)
        return await connection.run(
            script_str,
            check=False,
            timeout=self._request_timeout,
            env=env_params,
        )

    def remote_exec(
        self,
        script: Iterable[str],
        config: dict,
        env_params: dict,
    ) -> Tuple["Status", dict]:
        """
        Start running a command on remote host OS.

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
            ],
        )
        config["asyncRemoteExecResultsFuture"] = self._run_coroutine(
            self._run_cmd(
                config,
                script,
                env_params,
            )
        )
        return (Status.PENDING, config)

    def get_remote_exec_results(self, config: dict) -> Tuple["Status", dict]:
        """
        Get the results of the asynchronously running command.

        Parameters
        ----------
        config : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            Must have the "asyncRemoteExecResultsFuture" key to get the results.
            If the key is not present, return Status.PENDING.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
        """
        future = config.get("asyncRemoteExecResultsFuture")
        if not future:
            raise ValueError("Missing 'asyncRemoteExecResultsFuture'.")
        assert isinstance(future, Future)
        result = None
        try:
            result = future.result(timeout=self._request_timeout)
            assert isinstance(result, SSHCompletedProcess)
            stdout = result.stdout.decode() if isinstance(result.stdout, bytes) else result.stdout
            stderr = result.stderr.decode() if isinstance(result.stderr, bytes) else result.stderr
            return (
                (
                    Status.SUCCEEDED
                    if result.exit_status == 0 and result.returncode == 0
                    else Status.FAILED
                ),
                {
                    "stdout": stdout,
                    "stderr": stderr,
                    "ssh_completed_process_result": result,
                },
            )
        except (ConnectionLost, DisconnectError, ProcessError, TimeoutError) as ex:
            _LOG.error("Failed to get remote exec results: %s", ex)
            return (Status.FAILED, {"result": result})

    def _exec_os_op(self, cmd_opts_list: List[str], params: dict) -> Tuple[Status, dict]:
        """
        _summary_

        Parameters
        ----------
        cmd_opts_list : List[str]
            List of commands to try to execute.
        params : dict
            The params used to connect to the host.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "ssh_hostname",
            ],
        )
        cmd_opts = " ".join([f"'{cmd}'" for cmd in cmd_opts_list])
        script = rf"""
            if [[ $EUID -ne 0 ]]; then
                sudo=$(command -v sudo)
                sudo=${{sudo:+$sudo -n}}
            fi

            set -x
            for cmd in {cmd_opts}; do
                $sudo /bin/bash -c "$cmd" && exit 0
            done

            echo 'ERROR: Failed to shutdown/reboot the system.'
            exit 1
        """
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
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        cmd_opts_list = [
            "shutdown -h now",
            "poweroff",
            "halt -p",
            "systemctl poweroff",
        ]
        return self._exec_os_op(cmd_opts_list=cmd_opts_list, params=params)

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
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        cmd_opts_list = [
            "shutdown -r now",
            "reboot",
            "halt --reboot",
            "systemctl reboot",
            "kill -KILL 1; kill -KILL -1" if force else "kill -TERM 1; kill -TERM -1",
        ]
        return self._exec_os_op(cmd_opts_list=cmd_opts_list, params=params)

    def wait_os_operation(self, params: dict) -> Tuple[Status, dict]:
        """
        Waits for a pending operation on an OS to resolve to SUCCEEDED or FAILED. Return
        TIMED_OUT when timing out.

        Parameters
        ----------
        params: dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            Must have the "asyncRemoteExecResultsFuture" key to get the results.
            If the key is not present, return Status.PENDING.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
            Result is info on the operation runtime if SUCCEEDED, otherwise {}.
        """
        return self.get_remote_exec_results(params)
