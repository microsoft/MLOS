#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Helper functions to work with temp files locally on the scheduler side."""

import abc
import logging
import os
from contextlib import nullcontext
from string import Template
from tempfile import TemporaryDirectory
from typing import Any, Callable, Dict, List, Optional, Union

from mlos_bench.services.base_service import Service

_LOG = logging.getLogger(__name__)


class TempDirContextService(Service, metaclass=abc.ABCMeta):
    """
    A *base* service class that provides a method to create a temporary directory
    context for local scripts.

    It is inherited by LocalExecService and MockLocalExecService. This class is not
    supposed to be used as a standalone service.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        global_config: Optional[Dict[str, Any]] = None,
        parent: Optional[Service] = None,
        methods: Union[Dict[str, Callable], List[Callable], None] = None,
    ):
        """
        Create a new instance of a service that provides temporary directory context for
        local exec service.

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
            config,
            global_config,
            parent,
            self.merge_methods(methods, [self.temp_dir_context]),
        )
        self._temp_dir = self.config.get("temp_dir")
        if self._temp_dir:
            # expand globals
            self._temp_dir = Template(self._temp_dir).safe_substitute(global_config or {})
            # and resolve the path to absolute path
            self._temp_dir = self._config_loader_service.resolve_path(self._temp_dir)
        _LOG.info("%s: temp dir: %s", self, self._temp_dir)

    def temp_dir_context(
        self,
        path: Optional[str] = None,
    ) -> Union[TemporaryDirectory, nullcontext]:
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
        temp_dir = path or self._temp_dir
        if temp_dir is None:
            return TemporaryDirectory()
        os.makedirs(temp_dir, exist_ok=True)
        return nullcontext(temp_dir)
