#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Protocol interface for Service types that provide helper functions to run scripts and
commands locally on the scheduler side.
"""

import contextlib
import tempfile
from collections.abc import Iterable, Mapping
from typing import Protocol, runtime_checkable

from mlos_bench.tunables.tunable import TunableValue


@runtime_checkable
class SupportsLocalExec(Protocol):
    """
    Protocol interface for a collection of methods to run scripts and commands in an
    external process on the node acting as the scheduler.

    Can be useful for data processing due to reduced dependency management complications
    vs the target environment. Used in LocalEnv and provided by LocalExecService.
    """

    def local_exec(
        self,
        script_lines: Iterable[str],
        env: Mapping[str, TunableValue] | None = None,
        cwd: str | None = None,
    ) -> tuple[int, str, str]:
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

    def temp_dir_context(
        self,
        path: str | None = None,
    ) -> tempfile.TemporaryDirectory | contextlib.nullcontext:
        """
        Create a temp directory or use the provided path.

        Parameters
        ----------
        path : str
            A path to the temporary directory. Create a new one if None.

        Returns
        -------
        temp_dir_context : tempfile.TemporaryDirectory
            Temporary directory context to use in the `with` clause.
        """
