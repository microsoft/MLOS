#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helper functions to run scripts and commands locally on the scheduler side.
"""

import os
import sys
import errno
import tempfile
import contextlib
import shlex
import subprocess
import logging

from typing import Optional, Tuple, List, Dict, Protocol, runtime_checkable

from mlos_bench.service.base_service import Service

_LOG = logging.getLogger(__name__)


@runtime_checkable
class LocalExec(Protocol):
    def local_exec(self, script_lines: List[str],
                   env: Optional[Dict[str, str]] = None,
                   cwd: Optional[str] = None,
                   return_on_error: bool = False) -> Tuple[int, str, str]:
        ...


class LocalExecService(Service, LocalExec):
    """
    Collection of methods to run scripts and commands in an external process
    on the node acting as the scheduler. Can be useful for data processing
    due to reduced dependency management complications vs the target environment.
    """

    def __init__(self, config: Optional[dict] = None, parent: Optional[Service] = None):
        """
        Create a new instance of a service to run scripts locally.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains parameters for the service.
            (E.g., root path for config files, etc.)
        parent : Service
            An optional parent service that can provide mixin functions.
        """
        super().__init__(config, parent)
        self._temp_dir = self.config.get("temp_dir")
        self.register([self.temp_dir_context, self.local_exec])

    def temp_dir_context(self, path: Optional[str] = None):
        """
        Create a temp directory or use the provided path.

        Parameters
        ----------
        path : str
            A path to the temporary directory. Create a new one if None.

        Returns
        -------
        temp_dir_context : TemporaryDirectory
            Temporary directory context to use in the `with` clause.
        """
        if path is None and self._temp_dir is None:
            return tempfile.TemporaryDirectory()
        return contextlib.nullcontext(path or self._temp_dir)

    def local_exec(self, script_lines: List[str],
                   env: Optional[Dict[str, str]] = None,
                   cwd: Optional[str] = None,
                   return_on_error: bool = False) -> Tuple[int, str, str]:
        """
        Execute the script lines from `script_lines` in a local process.

        Parameters
        ----------
        script_lines : List[str]
            Lines of the script to run locally.
            Treat every line as a separate command to run.
        env : Dict[str, str]
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

        stdout = "\n".join(stdout_list)
        stderr = "\n".join(stderr_list)

        _LOG.debug("Run: stdout:\n%s", stdout)
        _LOG.debug("Run: stderr:\n%s", stderr)

        return (return_code, stdout, stderr)

    def _local_exec_script(self, script_line: str,
                           env: Dict[str, str], cwd: str) -> Tuple[int, str, str]:
        """
        Execute the script from `script_path` in a local process.

        Parameters
        ----------
        script_line : str
            Line of the script to tun in the local process.
        args : List[str]
            Command line arguments for the script.
        env : Dict[str, str]
            Environment variables.
        cwd : str
            Work directory to run the script at.

        Returns
        -------
        (return_code, stdout, stderr) : (int, str, str)
            A 3-tuple of return code, stdout, and stderr of the script process.
        """
        cmd = shlex.split(script_line)
        script_path = self._parent.resolve_path(cmd[0])
        if os.path.exists(script_path):
            script_path = os.path.abspath(script_path)

        cmd = [script_path] + cmd[1:]
        if script_path.strip().lower().endswith(".py"):
            cmd = [sys.executable] + cmd

        if env:
            env = {key: str(val) for (key, val) in env.items()}
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

            proc = subprocess.run(cmd, env=env, cwd=cwd, shell=True,
                                  text=True, check=False, capture_output=True)

            _LOG.debug("Run: return code = %d", proc.returncode)
            return (proc.returncode, proc.stdout, proc.stderr)

        except FileNotFoundError as ex:
            _LOG.warning("File not found: %s", cmd, exc_info=ex)

        return (errno.ENOENT, "", "File not found")
