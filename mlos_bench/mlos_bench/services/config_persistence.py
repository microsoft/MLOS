#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helper functions to load, instantiate, and serialize Python objects
that encapsulate benchmark environments, tunable parameters, and
service functions.
"""

import os
import sys

import json    # For logging only
import logging

from typing import Any, Dict, Iterable, List, Optional, Union, Tuple, Type

import json5   # To read configs with comments and other JSON5 syntax features

from mlos_bench.environments.base_environment import Environment
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.config_loader_type import SupportsConfigLoading
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import instantiate_from_config, BaseTypeVar

_LOG = logging.getLogger(__name__)


class ConfigPersistenceService(Service, SupportsConfigLoading):
    """
    Collection of methods to deserialize the Environment, Service, and TunableGroups objects.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None,
                 parent: Optional[Service] = None):
        """
        Create a new instance of config persistence service.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains parameters for the service.
            (E.g., root path for config files, etc.)
        parent : Service
            An optional parent service that can provide mixin functions.
        """
        super().__init__(config, parent)
        self._config_path = self.config.get("config_path", [])
        self._config_loader_service = self

        # Register methods that we want to expose to the Environment objects.
        self.register([
            self.resolve_path,
            self.load_config,
            self.prepare_class_load,
            self.build_service,
            self.build_environment,
            self.load_services,
            self.load_environment,
            self.load_environment_list,
        ])

    def resolve_path(self, file_path: str,
                     extra_paths: Optional[Iterable[str]] = None) -> str:
        """
        Prepend the suitable `_config_path` to `path` if the latter is not absolute.
        If `_config_path` is `None` or `path` is absolute, return `path` as is.

        Parameters
        ----------
        file_path : str
            Path to the input config file.
        extra_paths : Iterable[str]
            Additional directories to prepend to the list of search paths.

        Returns
        -------
        path : str
            An actual path to the config or script.
        """
        path_list = (extra_paths or []) + self._config_path
        _LOG.debug("Resolve path: %s in: %s", file_path, path_list)
        if not os.path.isabs(file_path):
            for path in path_list:
                full_path = os.path.join(path, file_path)
                if os.path.exists(full_path):
                    _LOG.debug("Path resolved: %s", full_path)
                    return full_path
        _LOG.debug("Path not resolved: %s", file_path)
        return file_path

    def load_config(self, json_file_name: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Load JSON config file. Search for a file relative to `_config_path`
        if the input path is not absolute.
        This method is exported to be used as a service.

        Parameters
        ----------
        json_file_name : str
            Path to the input config file.

        Returns
        -------
        config : Union[dict, List[dict]]
            Free-format dictionary that contains the configuration.
        """
        json_file_name = self.resolve_path(json_file_name)
        _LOG.info("Load config: %s", json_file_name)
        with open(json_file_name, mode='r', encoding='utf-8') as fh_json:
            return json5.load(fh_json)  # type: ignore[no-any-return]

    def prepare_class_load(self, config: Dict[str, Any],
                           global_config: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Extract the class instantiation parameters from the configuration.
        Mix-in the global parameters and resolve the local file system paths,
        where it is required.

        Parameters
        ----------
        config : dict
            Configuration of the optimizer.
        global_config : dict
            Global configuration parameters (optional).

        Returns
        -------
        (class_name, class_config) : (str, dict)
            Name of the class to instantiate and its configuration.
        """
        class_name = config["class"]
        class_config = config.setdefault("config", {})

        if global_config is None:
            global_config = {}

        class_params = set(class_config)
        for key in class_params.intersection(global_config):
            class_config[key] = global_config[key]

        for key in class_params.intersection(config.get("resolve_path", [])):
            if isinstance(class_config[key], str):
                class_config[key] = self.resolve_path(class_config[key])
            elif isinstance(class_config[key], (list, tuple)):
                class_config[key] = [self.resolve_path(path) for path in class_config[key]]
            else:
                raise ValueError(f"Parameter {key} must be a string or a list")

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Instantiating: %s with config:\n%s",
                       class_name, json.dumps(class_config, indent=2))

        return (class_name, class_config)

    def build_generic(self, *,
                      base_cls: Type[BaseTypeVar],
                      tunables: TunableGroups,
                      service: Service,
                      config: Dict[str, Any],
                      global_config: Optional[Dict[str, Any]] = None) -> BaseTypeVar:
        """
        Generic instantiation of mlos_bench objects like Storage and Optimizer
        that depend on Service and TunableGroups.

        A class *MUST* have a constructor that takes exactly three arguments:
        (tunables, service, config)

        Parameters
        ----------
        base_cls : ClassType
            A base class of the object to instantiate.
        tunables : TunableGroups
            Tunable parameters of the environment. We need them to validate the
            configurations of merged-in experiments and restored/pending trials.
        service: Service
            An optional service object (e.g., providing methods to load config files, etc.)
        config : dict
            Configuration of the class to instantiate, as loaded from JSON.
        global_config : dict
            Global configuration parameters (optional).

        Returns
        -------
        inst : Any
            A new instance of the `cls` class.
        """
        (class_name, class_config) = self.prepare_class_load(config, global_config)
        inst = instantiate_from_config(base_cls, class_name, tunables, service, class_config)
        _LOG.info("Created: %s", inst)
        return inst

    def build_environment(self, config: Dict[str, Any],
                          tunables: TunableGroups,
                          global_config: Optional[Dict[str, Any]] = None,
                          service: Optional[Service] = None) -> Environment:
        """
        Factory method for a new environment with a given config.

        Parameters
        ----------
        config : dict
            A dictionary with three mandatory fields:
                "name": Human-readable string describing the environment;
                "class": FQN of a Python class to instantiate;
                "config": Free-format dictionary to pass to the constructor.
        tunables : TunableGroups
            A (possibly empty) collection of groups of tunable parameters for
            all environments.
        global_config : dict
            Global parameters to add to the environment config.
        service: Service
            An optional service object (e.g., providing methods to
            deploy or reboot a VM, etc.).

        Returns
        -------
        env : Environment
            An instance of the `Environment` class initialized with `config`.
        """
        env_name = config["name"]
        (env_class, env_config) = self.prepare_class_load(config)

        env_services_path = config.get("include_services")
        if env_services_path is not None:
            service = self.load_services(env_services_path, global_config, service)

        env_tunables_path = config.get("include_tunables")
        if env_tunables_path is not None:
            tunables = self._load_tunables(env_tunables_path, tunables)

        _LOG.debug("Creating env: %s :: %s", env_name, env_class)
        env = Environment.new(env_name=env_name, class_name=env_class,
                              config=env_config, global_config=global_config,
                              tunables=tunables, service=service)

        _LOG.info("Created env: %s :: %s", env_name, env)
        return env

    def _build_standalone_service(self, config: Dict[str, Any],
                                  global_config: Optional[Dict[str, Any]] = None,
                                  parent: Optional[Service] = None) -> Service:
        """
        Factory method for a new service with a given config.

        Parameters
        ----------
        config : dict
            A dictionary with two mandatory fields:
                "class": FQN of a Python class to instantiate;
                "config": Free-format dictionary to pass to the constructor.
        global_config : dict
            Global parameters to add to the service config.
        parent: Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        svc : Service
            An instance of the `Service` class initialized with `config`.
        """
        (svc_class, svc_config) = self.prepare_class_load(config, global_config)
        service = Service.new(svc_class, svc_config, parent)
        _LOG.info("Created service: %s", service)
        return service

    def _build_composite_service(self, config_list: Iterable[Dict[str, Any]],
                                 global_config: Optional[Dict[str, Any]] = None,
                                 parent: Optional[Service] = None) -> Service:
        """
        Factory method for a new service with a given config.

        Parameters
        ----------
        config_list : a list of dict
            A list where each element is a dictionary with 2 mandatory fields:
                "class": FQN of a Python class to instantiate;
                "config": Free-format dictionary to pass to the constructor.
        global_config : dict
            Global parameters to add to the service config.
        parent: Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        svc : Service
            An instance of the `Service` class that is a combination of all
            services from the list plus the parent mix-in.
        """
        service = Service()
        if parent:
            service.register(parent.export())

        for config in config_list:
            service.register(self._build_standalone_service(
                config, global_config, service).export())

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Created mix-in service:\n%s", "\n".join(
                f'  "{key}": {val}' for (key, val) in service.export().items()))

        return service

    def build_service(self,
                      config: Union[Dict[str, Any], List[Dict[str, Any]]],
                      global_config: Optional[Dict[str, Any]] = None,
                      parent: Optional[Service] = None) -> Service:
        """
        Factory method for a new service with a given config.

        Parameters
        ----------
        config : dict or list of dict
            A list where each element is a dictionary with 2 mandatory fields:
                "class": FQN of a Python class to instantiate;
                "config": Free-format dictionary to pass to the constructor.
        global_config : dict
            Global parameters to add to the service config.
        parent: Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        svc : Service
            An instance of the `Service` class that is a combination of all
            services from the list plus the parent mix-in.
        """
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Build service from config:\n%s",
                       json.dumps(config, indent=2))

        if isinstance(config, dict):
            if parent is None:
                return self._build_standalone_service(config, global_config)
            config = [config]

        return self._build_composite_service(config, global_config, parent)

    def load_environment(self, json_file_name: str,
                         tunables: TunableGroups,
                         global_config: Optional[Dict[str, Any]] = None,
                         service: Optional[Service] = None) -> Environment:
        """
        Load and build new environment from the config file.

        Parameters
        ----------
        json_file_name : str
            The environment JSON configuration file.
        tunables : TunableGroups
            A (possibly empty) collection of tunables to add to the environment.
        global_config : dict
            Global parameters to add to the environment config.
        service : Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        env : Environment
            A new benchmarking environment.
        """
        config = self.load_config(json_file_name)
        assert isinstance(config, dict)
        return self.build_environment(config, tunables, global_config, service)

    def load_environment_list(self, json_file_name: str,
                              tunables: TunableGroups,
                              global_config: Optional[Dict[str, Any]] = None,
                              service: Optional[Service] = None) -> List[Environment]:
        """
        Load and build a list of environments from the config file.

        Parameters
        ----------
        json_file_name : str
            The environment JSON configuration file.
            Can contain either one environment or a list of environments.
        tunables : TunableGroups
            An (possibly empty) collection of tunables to add to the environment.
        global_config : dict
            Global parameters to add to the environment config.
        service : Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        env : List[Environment]
            A list of new benchmarking environments.
        """
        config_list = self.load_config(json_file_name)
        if isinstance(config_list, dict):
            config_list = [config_list]
        return [
            self.build_environment(config, tunables, global_config, service)
            for config in config_list
        ]

    def load_services(self, json_file_names: Iterable[str],
                      global_config: Optional[Dict[str, Any]] = None,
                      parent: Optional[Service] = None) -> Service:
        """
        Read the configuration files and bundle all service methods
        from those configs into a single Service object.

        Parameters
        ----------
        json_file_names : list of str
            A list of service JSON configuration files.
        global_config : dict
            Global parameters to add to the service config.
        parent : Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        service : Service
            A collection of service methods.
        """
        _LOG.info("Load services: %s parent: %s",
                  json_file_names, parent.__class__.__name__)
        service = Service(global_config, parent)
        for fname in json_file_names:
            config = self.load_config(fname)
            service.register(self.build_service(config, global_config, service).export())
        return service

    def _load_tunables(self, json_file_names: Iterable[str],
                       parent: TunableGroups) -> TunableGroups:
        """
        Load a collection of tunable parameters from JSON files into the parent
        TunableGroup.

        This helps allow standalone environment configs to reference
        overlapping tunable groups configs but still allow combining them into
        a single instance that each environment can reference.

        Parameters
        ----------
        json_file_names : list of str
            A list of JSON files to load.
        parent : TunableGroups
            A (possibly empty) collection of tunables to add to the new collection.

        Returns
        -------
        tunables : TunableGroup
            The larger collection of tunable parameters.
        """
        _LOG.info("Load tunables: '%s'", json_file_names)
        for fname in json_file_names:
            config = self.load_config(fname)
            assert isinstance(config, dict)
            parent.merge(TunableGroups(config))
        return parent
