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

from typing import Tuple, List, Dict

import pandas

from mlos_bench.environment.status import Status
from mlos_bench.environment.base_service import Service

_LOG = logging.getLogger(__name__)


class LocalExecService(Service):
    """
    Collection of methods to run scripts and commands in an external process
    on the node acting as the scheduler. Can be useful for data processing
    due to reduced dependency management complications vs the target environment.
    """

    def __init__(self, config: dict = None, parent: Service = None):
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

        # Register methods to expose to the Environment objects.
        self.register([self.local_exec])

    def local_exec(self, script_lines: List[str], env: Dict[str, str] = None,
                   cwd: str = None, output_csv_file: str = None,
                   return_on_error: bool = False) -> Tuple[Status, str]:
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
        output_csv_file : str
            Output file to read as pandas DataFrame. (optional)
        return_on_error : bool
            If True, stop running script lines on first non-zero return code.
            The default is False.

        Returns
        -------
        (return_code, output) : (Status, str or DataFrame)
            A 2-tuple of status and output of the script process.
        """
        if cwd is None and self._temp_dir is None:
            temp_dir_context = tempfile.TemporaryDirectory()
        else:
            temp_dir_context = contextlib.nullcontext(cwd or self._temp_dir)

        output = None
        (return_code, stdout_list, stderr_list) = (0, [], [])
        with temp_dir_context as temp_dir:
            _LOG.debug("Run in directory: %s", temp_dir)
            for line in script_lines:
                cmd = shlex.split(line)
                (return_code, stdout, stderr) = self._local_exec_script(
                    cmd[0], cmd[1:], env, temp_dir)
                stdout_list.append(stdout)
                stderr_list.append(stderr)
                if return_code != 0 and return_on_error:
                    break
            if output_csv_file:
                if not os.path.exists(output_csv_file):
                    output_csv_file = os.path.join(temp_dir, output_csv_file)
                output = pandas.read_csv(output_csv_file)
            else:
                output = "\n".join(stdout_list)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Run: stdout:\n%s", output)
            _LOG.debug("Run: stderr:\n%s", "\n".join(stderr_list))

        return (Status.SUCCEEDED if return_code == 0 else Status.FAILED, output)

    def _local_exec_script(self, script_path: str, args: List[str],
                           env: Dict[str, str], cwd: str) -> Tuple[int, str, str]:
        """
        Execute the script from `script_path` in a local process.

        Parameters
        ----------
        script_path : str
            Path to the script to run.
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
        cmd = [self._parent.resolve_path(script_path)] + args
        if script_path.strip().lower().endswith(".py"):
            cmd = [sys.executable] + cmd

        if _LOG.isEnabledFor(logging.INFO):
            _LOG.info("Run: '%s'", " ".join(cmd))

        try:
            if sys.platform != 'win32':
                cmd = [" ".join(cmd)]
            proc = subprocess.run(cmd, env=env, cwd=cwd, shell=True,
                                  text=True, check=False, capture_output=True)

            _LOG.debug("Run: exit code = %d", proc.returncode)
            return (proc.returncode, proc.stdout, proc.stderr)

        except FileNotFoundError as ex:
            _LOG.warning("File not found: %s", cmd, exc_info=ex)

        return (errno.ENOENT, "", "File not found")
