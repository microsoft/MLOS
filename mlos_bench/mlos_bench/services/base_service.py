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
                 parent: Optional["Service"] = None,
                 methods: Union[Dict[str, Callable], List[Callable], None] = None):
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
        methods : Union[Dict[str, Callable], List[Callable], None]
            New methods to register with the service.
        """
        self.config = config or {}
        self._validate_json_config(self.config)
        self._parent = parent
        self._services: Dict[str, Callable] = {}

        if parent:
            self.register(parent.export())
        if methods:
            self.register(methods)

        self._config_loader_service: SupportsConfigLoading
        if parent and isinstance(parent, SupportsConfigLoading):
            self._config_loader_service = parent

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Service: %s Config:\n%s", self, json.dumps(self.config, indent=2))
            _LOG.debug("Service: %s Globals:\n%s", self, json.dumps(global_config or {}, indent=2))
            _LOG.debug("Service: %s Parent: %s", self, parent.pprint() if parent else None)

    @staticmethod
    def merge_methods(ext_methods: Union[Dict[str, Callable], List[Callable], None],
                      local_methods: Union[Dict[str, Callable], List[Callable]]) -> Dict[str, Callable]:
        """
        Merge methods from the external caller with the local ones.
        This function is usually called by the derived class constructor
        just before invoking the constructor of the base class.
        """
        if isinstance(local_methods, dict):
            local_methods = local_methods.copy()
        else:
            local_methods = {svc.__name__: svc for svc in local_methods}

        if not ext_methods:
            return local_methods

        if not isinstance(ext_methods, dict):
            ext_methods = {svc.__name__: svc for svc in ext_methods}

        local_methods.update(ext_methods)
        return local_methods

    def _validate_json_config(self, config: dict) -> None:
        """
        Reconstructs a basic json config that this class might have been
        instantiated from in order to validate configs provided outside the
        file loading mechanism.
        """
        if self.__class__ == Service:
            # Skip over the case where instantiate a bare base Service class in order to build up a mix-in.
            assert config == {}
            return
        json_config: dict = {
            "class": self.__class__.__module__ + "." + self.__class__.__name__,
        }
        if config:
            json_config["config"] = config
        ConfigSchema.SERVICE.validate(json_config)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}@{hex(id(self))}"

    def pprint(self) -> str:
        """
        Produce a human-readable string listing all public methods of the service.
        """
        return f"{self} ::\n" + "\n".join(
            f'  "{key}": {getattr(val, "__self__", "stand-alone")}'
            for (key, val) in self._services.items()
        )

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

        self._services.update(services)
        self.__dict__.update(self._services)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Added methods to: %s", self.pprint())

    def export(self) -> Dict[str, Callable]:
        """
        Return a dictionary of functions available in this service.

        Returns
        -------
        services : dict
            A dictionary of string -> function pairs.
        """
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Export methods from: %s", self.pprint())

        return self._services
