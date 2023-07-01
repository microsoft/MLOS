#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helper functions to work with temp files locally on the scheduler side.
"""

import abc
import logging
from contextlib import nullcontext
from tempfile import TemporaryDirectory
from typing import Any, Dict, Optional, Union

from mlos_bench.services.base_service import Service

_LOG = logging.getLogger(__name__)


class TempDirContextService(Service, metaclass=abc.ABCMeta):
    """
    A *base* service class that provides a method to create a temporary
    directory context for local scripts.

    It is inherited by LocalExecService and MockLocalExecService.
    This class is not supposed to be used as a standalone service.
    """

    def __init__(self, config: Optional[dict] = None,
                 global_config: Optional[Dict[str, Any]] = None,
                 parent: Optional[Service] = None):
        """
        Create a new instance of a service that provides temporary directory context
        for local exec service.

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
        self._temp_dir = self.config.get("temp_dir")
        self.register([self.temp_dir_context])

    def temp_dir_context(self, path: Optional[str] = None) -> Union[TemporaryDirectory, nullcontext]:
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
            return TemporaryDirectory()
        return nullcontext(path or self._temp_dir)
