#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for mocking local exec.
"""

import contextlib
import logging
import tempfile

from typing import Iterable, Mapping, Optional, Tuple, Union, TYPE_CHECKING

from mlos_bench.services.base_service import Service
from mlos_bench.services.types.local_exec_type import SupportsLocalExec

if TYPE_CHECKING:
    from mlos_bench.tunables.tunable import TunableValue

_LOG = logging.getLogger(__name__)


class MockLocalExecService(Service, SupportsLocalExec):
    """
    Mock methods for LocalExecService testing.
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
        self.register([
            self.temp_dir_context,
            self.local_exec,
        ])

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
        if path is None and self._temp_dir is None:
            return tempfile.TemporaryDirectory()
        return contextlib.nullcontext(path or self._temp_dir)

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
        return (0, "", "")
