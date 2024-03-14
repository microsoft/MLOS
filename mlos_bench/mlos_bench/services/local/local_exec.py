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

from string import Template
from typing import (
    Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple, TYPE_CHECKING, Union
)

from mlos_bench.os_environ import environ
from mlos_bench.services.base_service import Service
from mlos_bench.services.local.temp_dir_context import TempDirContextService
from mlos_bench.services.types.local_exec_type import SupportsLocalExec

if TYPE_CHECKING:
    from mlos_bench.tunables.tunable import TunableValue

_LOG = logging.getLogger(__name__)


def split_cmdline(cmdline: str) -> Iterable[List[str]]:
    """
    A single command line may contain multiple commands separated by
    special characters (e.g., &&, ||, etc.) so further split the
    commandline into an array of subcommand arrays.

    Parameters
    ----------
    cmdline: str
        The commandline to split.

    Yields
    ------
    Iterable[List[str]]
        A list of subcommands or separators, each one a list of tokens.
        Can be rejoined as a flattened array.
    """
    cmdline_tokens = shlex.shlex(cmdline, posix=True, punctuation_chars=True)
    cmdline_tokens.whitespace_split = True
    subcmd = []
    for token in cmdline_tokens:
        if token[0] not in cmdline_tokens.punctuation_chars:
            subcmd.append(token)
        else:
            # Separator encountered. Yield any non-empty previous subcmd we accumulated.
            if subcmd:
                yield subcmd
            # Also return the separators.
            yield [token]
            subcmd = []
    # Return the trailing subcommand.
    if subcmd:
        yield subcmd


class LocalExecService(TempDirContextService, SupportsLocalExec):
    """
    Collection of methods to run scripts and commands in an external process
    on the node acting as the scheduler. Can be useful for data processing
    due to reduced dependency management complications vs the target environment.
    """

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 global_config: Optional[Dict[str, Any]] = None,
                 parent: Optional[Service] = None,
                 methods: Union[Dict[str, Callable], List[Callable], None] = None):
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
        methods : Union[Dict[str, Callable], List[Callable], None]
            New methods to register with the service.
        """
        super().__init__(
            config, global_config, parent,
            self.merge_methods(methods, [self.local_exec])
        )
        self.abort_on_error = self.config.get("abort_on_error", True)

    def local_exec(self, script_lines: Iterable[str],
                   env: Optional[Mapping[str, "TunableValue"]] = None,
                   cwd: Optional[str] = None) -> Tuple[int, str, str]:
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
                if return_code != 0 and self.abort_on_error:
                    break

        stdout = "".join(stdout_list)
        stderr = "".join(stderr_list)

        _LOG.debug("Run: stdout:\n%s", stdout)
        _LOG.debug("Run: stderr:\n%s", stderr)

        return (return_code, stdout, stderr)

    def _resolve_cmdline_script_path(self, subcmd_tokens: List[str]) -> List[str]:
        """
        Resolves local script path (first token) in the (sub)command line
        tokens to its full path.

        Parameters
        ----------
        subcmd_tokens : List[str]
            The previously split tokens of the subcmd.

        Returns
        -------
        List[str]
            A modified sub command line with the script paths resolved.
        """
        script_path = self.config_loader_service.resolve_path(subcmd_tokens[0])
        # Special case check for lone `.` which means both `source` and
        # "current directory" (which isn't executable) in posix shells.
        if os.path.exists(script_path) and os.path.isfile(script_path):
            # If the script exists, use it.
            subcmd_tokens[0] = os.path.abspath(script_path)
            # Also check if it is a python script and prepend the currently
            # executing python executable path to avoid requiring
            # executable mode bits or a shebang.
            if script_path.strip().lower().endswith(".py"):
                subcmd_tokens.insert(0, sys.executable)
        return subcmd_tokens

    def _local_exec_script(self, script_line: str,
                           env_params: Optional[Mapping[str, "TunableValue"]],
                           cwd: str) -> Tuple[int, str, str]:
        """
        Execute the script from `script_path` in a local process.

        Parameters
        ----------
        script_line : str
            Line of the script to run in the local process.
        env_params : Mapping[str, Union[int, float, str]]
            Environment variables.
        cwd : str
            Work directory to run the script at.

        Returns
        -------
        (return_code, stdout, stderr) : (int, str, str)
            A 3-tuple of return code, stdout, and stderr of the script process.
        """
        # Split the command line into set of subcmd tokens.
        # For each subcmd, perform path resolution fixups for any scripts being executed.
        subcmds = split_cmdline(script_line)
        subcmds = [self._resolve_cmdline_script_path(subcmd) for subcmd in subcmds]
        # Finally recombine all of the fixed up subcmd tokens into the original.
        cmd = [token for subcmd in subcmds for token in subcmd]

        env: Dict[str, str] = {}
        if env_params:
            env = {key: str(val) for (key, val) in env_params.items()}

        if sys.platform == 'win32':
            # A hack to run Python on Windows with env variables set:
            env_copy = environ.copy()
            env_copy["PYTHONPATH"] = ""
            env_copy.update(env)
            env = env_copy

        try:
            if sys.platform != 'win32':
                cmd = [" ".join(cmd)]

            _LOG.info("Run: %s", cmd)
            if _LOG.isEnabledFor(logging.DEBUG):
                _LOG.debug("Expands to: %s", Template(" ".join(cmd)).safe_substitute(env))
                _LOG.debug("Current working dir: %s", cwd)

            proc = subprocess.run(cmd, env=env or None, cwd=cwd, shell=True,
                                  text=True, check=False, capture_output=True)

            _LOG.debug("Run: return code = %d", proc.returncode)
            return (proc.returncode, proc.stdout, proc.stderr)

        except FileNotFoundError as ex:
            _LOG.warning("File not found: %s", cmd, exc_info=ex)

        return (errno.ENOENT, "", "File not found")
