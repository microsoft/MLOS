#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Base class for the service mix-ins."""

import json
import logging
from types import TracebackType
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

from typing_extensions import Literal

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.services.types.config_loader_type import SupportsConfigLoading
from mlos_bench.util import instantiate_from_config

_LOG = logging.getLogger(__name__)


class Service:
    """An abstract base of all Environment Services and used to build up mix-ins."""

    @classmethod
    def new(
        cls,
        class_name: str,
        config: Optional[Dict[str, Any]] = None,
        global_config: Optional[Dict[str, Any]] = None,
        parent: Optional["Service"] = None,
    ) -> "Service":
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

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        global_config: Optional[Dict[str, Any]] = None,
        parent: Optional["Service"] = None,
        methods: Union[Dict[str, Callable], List[Callable], None] = None,
    ):
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
        self._service_methods: Dict[str, Callable] = {}
        self._services: Set[Service] = set()
        self._service_contexts: List[Service] = []
        self._in_context = False

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
    def merge_methods(
        ext_methods: Union[Dict[str, Callable], List[Callable], None],
        local_methods: Union[Dict[str, Callable], List[Callable]],
    ) -> Dict[str, Callable]:
        """
        Merge methods from the external caller with the local ones.

        This function is usually called by the derived class constructor just before
        invoking the constructor of the base class.
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

    def __enter__(self) -> "Service":
        """
        Enter the Service mix-in context.

        Calls the _enter_context() method of all the Services registered under this one.
        """
        if self._in_context:
            # Multiple environments can share the same Service, so we need to
            # add a check and make this a re-entrant Service context.
            assert self._service_contexts
            assert all(svc._in_context for svc in self._services)
            return self
        self._service_contexts = [svc._enter_context() for svc in self._services]
        self._in_context = True
        return self

    def __exit__(
        self,
        ex_type: Optional[Type[BaseException]],
        ex_val: Optional[BaseException],
        ex_tb: Optional[TracebackType],
    ) -> Literal[False]:
        """
        Exit the Service mix-in context.

        Calls the _exit_context() method of all the Services registered under this one.
        """
        if not self._in_context:
            # Multiple environments can share the same Service, so we need to
            # add a check and make this a re-entrant Service context.
            assert not self._service_contexts
            assert all(not svc._in_context for svc in self._services)
            return False
        ex_throw = None
        for svc in reversed(self._service_contexts):
            try:
                svc._exit_context(ex_type, ex_val, ex_tb)
            # pylint: disable=broad-exception-caught
            except Exception as ex:
                _LOG.error("Exception while exiting Service context '%s': %s", svc, ex)
                ex_throw = ex
        self._service_contexts = []
        if ex_throw:
            raise ex_throw
        self._in_context = False
        return False

    def _enter_context(self) -> "Service":
        """
        Enters the context for this particular Service instance.

        Called by the base __enter__ method of the Service class so it can be used with
        mix-ins and overridden by subclasses.
        """
        assert not self._in_context
        self._in_context = True
        return self

    def _exit_context(
        self,
        ex_type: Optional[Type[BaseException]],
        ex_val: Optional[BaseException],
        ex_tb: Optional[TracebackType],
    ) -> Literal[False]:
        """
        Exits the context for this particular Service instance.

        Called by the base __enter__ method of the Service class so it can be used with
        mix-ins and overridden by subclasses.
        """
        # pylint: disable=unused-argument
        assert self._in_context
        self._in_context = False
        return False

    def _validate_json_config(self, config: dict) -> None:
        """Reconstructs a basic json config that this class might have been instantiated
        from in order to validate configs provided outside the file loading
        mechanism.
        """
        if self.__class__ == Service:
            # Skip over the case where instantiate a bare base Service class in
            # order to build up a mix-in.
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
        """Produce a human-readable string listing all public methods of the service."""
        return f"{self} ::\n" + "\n".join(
            f'  "{key}": {getattr(val, "__self__", "stand-alone")}'
            for (key, val) in self._service_methods.items()
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

        self._service_methods.update(services)
        self.__dict__.update(self._service_methods)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Added methods to: %s", self.pprint())

        # In order to get a list of all child contexts, we need to look at only
        # the bound methods that were not overridden by another mixin.
        # Then we inspect the internally bound __self__ variable to discover
        # which Service instance that method belongs too.
        # To do this we also

        # All service loading must happen prior to entering a context.
        assert not self._in_context
        assert not self._service_contexts
        self._services = {
            # Enumerate the Services that are bound to this instance in the
            # order they were added.
            # Unfortunately, by creating a set, we may destroy the ability to
            # preserve the context enter/exit order, but hopefully it doesn't
            # matter.
            svc_method.__self__
            for _, svc_method in self._service_methods.items()
            # Note: some methods are actually stand alone functions, so we need
            # to filter them out.
            if hasattr(svc_method, "__self__") and isinstance(svc_method.__self__, Service)
        }

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

        return self._service_methods
