#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helper functions to run scripts and commands locally on the scheduler side.
"""

import errno
import logging
import os
import shlex
import subprocess
import sys

from typing import Any, Dict, Iterable, Mapping, Optional, Tuple, TYPE_CHECKING

from mlos_bench.services.base_service import Service
from mlos_bench.services.local.temp_dir_context import TempDirContextService
from mlos_bench.services.types.local_exec_type import SupportsLocalExec

if TYPE_CHECKING:
    from mlos_bench.tunables.tunable import TunableValue

_LOG = logging.getLogger(__name__)


class LocalExecService(TempDirContextService, SupportsLocalExec):
    """
    Collection of methods to run scripts and commands in an external process
    on the node acting as the scheduler. Can be useful for data processing
    due to reduced dependency management complications vs the target environment.
    """

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 global_config: Optional[Dict[str, Any]] = None,
                 parent: Optional[Service] = None):
        """
        Create a new instance of a service to run scripts locally.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains parameters for the service.
            (E.g., root path for config files, etc.)
        global_config : dict
            Free-format dictionary of global parameters.
        parent : Service
            An optional parent service that can provide mixin functions.
        """
        super().__init__(config, global_config, parent)
        self.register([self.local_exec])

    def local_exec(self, script_lines: Iterable[str],
                   env: Optional[Mapping[str, "TunableValue"]] = None,
                   cwd: Optional[str] = None,
                   return_on_error: bool = False) -> Tuple[int, str, str]:
        """
        Execute the script lines from `script_lines` in a local process.

        Parameters
        ----------
        script_lines : Iterable[str]
            Lines of the script to run locally.
            Treat every line as a separate command to run.
        env : Mapping[str, Union[int, float, str]]
            Environment variables (optional).
        cwd : str
            Work directory to run the script at.
            If omitted, use `temp_dir` or create a temporary dir.
        return_on_error : bool
            If True, stop running script lines on first non-zero return code.
            The default is False.

        Returns
        -------
        (return_code, stdout, stderr) : (int, str, str)
            A 3-tuple of return code, stdout, and stderr of the script process.
        """
        (return_code, stdout_list, stderr_list) = (0, [], [])
        with self.temp_dir_context(cwd) as temp_dir:

            _LOG.debug("Run in directory: %s", temp_dir)

            for line in script_lines:
                (return_code, stdout, stderr) = self._local_exec_script(line, env, temp_dir)
                stdout_list.append(stdout)
                stderr_list.append(stderr)
                if return_code != 0 and return_on_error:
                    break

        stdout = "".join(stdout_list)
        stderr = "".join(stderr_list)

        _LOG.debug("Run: stdout:\n%s", stdout)
        _LOG.debug("Run: stderr:\n%s", stderr)

        return (return_code, stdout, stderr)

    def _local_exec_script(self, script_line: str,
                           env_params: Optional[Mapping[str, "TunableValue"]],
                           cwd: str) -> Tuple[int, str, str]:
        """
        Execute the script from `script_path` in a local process.

        Parameters
        ----------
        script_line : str
            Line of the script to tun in the local process.
        args : Iterable[str]
            Command line arguments for the script.
        env_params : Mapping[str, Union[int, float, str]]
            Environment variables.
        cwd : str
            Work directory to run the script at.

        Returns
        -------
        (return_code, stdout, stderr) : (int, str, str)
            A 3-tuple of return code, stdout, and stderr of the script process.
        """
        cmd = shlex.split(script_line)
        script_path = self.config_loader_service.resolve_path(cmd[0])
        if os.path.exists(script_path) and not os.path.isdir(script_path):
            script_path = os.path.abspath(script_path)
        else:
            script_path = cmd[0]  # rollback to the original value

        cmd = [script_path] + cmd[1:]
        if script_path.strip().lower().endswith(".py"):
            cmd = [sys.executable] + cmd

        env: Dict[str, str] = {}
        if env_params:
            env = {key: str(val) for (key, val) in env_params.items()}

        if sys.platform == 'win32':
            # A hack to run Python on Windows with env variables set:
            env_copy = os.environ.copy()
            env_copy["PYTHONPATH"] = ""
            env_copy.update(env)
            env = env_copy

        _LOG.info("Run: %s", cmd)

        try:
            if sys.platform != 'win32':
                cmd = [" ".join(cmd)]

            proc = subprocess.run(cmd, env=env or None, cwd=cwd, shell=True,
                                  text=True, check=False, capture_output=True)

            _LOG.debug("Run: return code = %d", proc.returncode)
            return (proc.returncode, proc.stdout, proc.stderr)

        except FileNotFoundError as ex:
            _LOG.warning("File not found: %s", cmd, exc_info=ex)

        return (errno.ENOENT, "", "File not found")
