#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Protocol interface for Service types that provide helper functions to run
scripts and commands locally on the scheduler side.
"""

from typing import Iterable, Mapping, Optional, Tuple, Union, Protocol, runtime_checkable

import tempfile
import contextlib

from mlos_bench.tunables.tunable import TunableValue


@runtime_checkable
class SupportsLocalExec(Protocol):
    """
    Protocol interface for a collection of methods to run scripts and commands
    in an external process on the node acting as the scheduler. Can be useful
    for data processing due to reduced dependency management complications vs
    the target environment.
    Used in LocalEnv and provided by LocalExecService.
    """

    def local_exec(self, script_lines: Iterable[str],
                   env: Optional[Mapping[str, TunableValue]] = None,
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

    def temp_dir_context(self, path: Optional[str] = None) -> Union[tempfile.TemporaryDirectory, contextlib.nullcontext]:
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
