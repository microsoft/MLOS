#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base class for the service mix-ins.
"""

import json
import logging

from typing import Any, Callable, Dict, List, Optional, Union

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.services.types.config_loader_type import SupportsConfigLoading
from mlos_bench.util import instantiate_from_config

_LOG = logging.getLogger(__name__)


class Service:
    """
    An abstract base of all Environment Services and used to build up mix-ins.
    """

    @classmethod
    def new(cls,
            class_name: str,
            config: Optional[Dict[str, Any]] = None,
            global_config: Optional[Dict[str, Any]] = None,
            parent: Optional["Service"] = None) -> "Service":
        """
        Factory method for a new service with a given config.

        Parameters
        ----------
        class_name: str
            FQN of a Python class to instantiate, e.g.,
            "mlos_bench.services.remote.azure.AzureVMService".
            Must be derived from the `Service` class.
        config : dict
            Free-format dictionary that contains the service configuration.
            It will be passed as a constructor parameter of the class
            specified by `class_name`.
        global_config : dict
            Free-format dictionary of global parameters.
        parent : Service
            A parent service that can provide mixin functions.

        Returns
        -------
        svc : Service
            An instance of the `Service` class initialized with `config`.
        """
        assert issubclass(cls, Service)
        return instantiate_from_config(cls, class_name, config, global_config, parent)

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 global_config: Optional[Dict[str, Any]] = None,
                 parent: Optional["Service"] = None):
        """
        Create a new service with a given config.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the service configuration.
            It will be passed as a constructor parameter of the class
            specified by `class_name`.
        global_config : dict
            Free-format dictionary of global parameters.
        parent : Service
            An optional parent service that can provide mixin functions.
        """
        self.config = config or {}
        print(self.config)
        if not isinstance(self, SupportsConfigLoading):
            ConfigSchema.SERVICE.validate(self.config)
        self._parent = parent
        self._services: Dict[str, Callable] = {}

        if parent:
            self.register(parent.export())

        self._config_loader_service: SupportsConfigLoading
        if parent and isinstance(parent, SupportsConfigLoading):
            self._config_loader_service = parent

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Service: %s Config:\n%s", self, json.dumps(self.config, indent=2))
            _LOG.debug("Service: %s Globals:\n%s", self, json.dumps(global_config or {}, indent=2))
            _LOG.debug("Service: %s Parent mixins: %s", self,
                       [] if parent is None else list(parent._services.keys()))

    def __repr__(self) -> str:
        return self.__class__.__name__

    @property
    def config_loader_service(self) -> SupportsConfigLoading:
        """
        Return a config loader service.

        Returns
        -------
        config_loader_service : SupportsConfigLoading
            A config loader service.
        """
        return self._config_loader_service

    def register(self, services: Union[Dict[str, Callable], List[Callable]]) -> None:
        """
        Register new mix-in services.

        Parameters
        ----------
        services : dict or list
            A dictionary of string -> function pairs.
        """
        if not isinstance(services, dict):
            services = {svc.__name__: svc for svc in services}

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Service: %s Add methods: %s",
                       self.__class__.__name__, list(services.keys()))

        # TODO? Throw a warning when an existing method is being overwritten?

        self._services.update(services)
        self.__dict__.update(self._services)

    def export(self) -> Dict[str, Callable]:
        """
        Return a dictionary of functions available in this service.

        Returns
        -------
        services : dict
            A dictionary of string -> function pairs.
        """
        return self._services
