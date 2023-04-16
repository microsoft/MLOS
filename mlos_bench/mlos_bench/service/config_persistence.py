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
import json    # For logging only
import logging

from typing import List, Optional, Union

import json5   # To read configs with comments and other JSON5 syntax features

from mlos_bench.util import prepare_class_load
from mlos_bench.environment.base_environment import Environment
from mlos_bench.service.base_service import Service
from mlos_bench.service.config_loader_type import SupportsConfigLoading
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class ConfigPersistenceService(Service, SupportsConfigLoading):
    """
    Collection of methods to deserialize the Environment, Service, and TunableGroups objects.
    """

    def __init__(self, config: Optional[dict] = None, parent: Optional[Service] = None):
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

        # Register methods that we want to expose to the Environment objects.
        self.register([
            self.resolve_path,
            self.load_config,
            ConfigPersistenceService.build_service,
            ConfigPersistenceService.build_tunables,
            self.build_environment,
            self.load_services,
            self.load_tunables,
            self.load_environment,
            self.load_environment_list,
        ])

    def resolve_path(self, file_path: str,
                     extra_paths: Optional[List[str]] = None) -> str:
        """
        Prepend the suitable `_config_path` to `path` if the latter is not absolute.
        If `_config_path` is `None` or `path` is absolute, return `path` as is.

        Parameters
        ----------
        file_path : str
            Path to the input config file.
        extra_paths : List[str]
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

    def load_config(self, json_file_name: str) -> Union[dict, List[dict]]:
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

    def build_environment(self, config: dict,
                          global_config: Optional[dict] = None,
                          tunables: Optional[TunableGroups] = None,
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
        global_config : dict
            Global parameters to add to the environment config.
        tunables : TunableGroups
            A collection of groups of tunable parameters for all environments.
        service: Service
            An optional service object (e.g., providing methods to
            deploy or reboot a VM, etc.).

        Returns
        -------
        env : Environment
            An instance of the `Environment` class initialized with `config`.
        """
        env_name = config["name"]
        (env_class, env_config) = prepare_class_load(config)

        env_services_path = config.get("include_services")
        if env_services_path is not None:
            service = self.load_services(env_services_path, global_config, service)

        env_tunables_path = config.get("include_tunables")
        if env_tunables_path is not None:
            tunables = self.load_tunables(env_tunables_path, tunables)

        _LOG.debug("Creating env: %s :: %s", env_name, env_class)
        env = Environment.new(env_name, env_class, env_config, global_config, tunables, service)

        _LOG.info("Created env: %s :: %s", env_name, env)
        return env

    @classmethod
    def _build_standalone_service(cls, config: dict,
                                  global_config: Optional[dict] = None,
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
        (svc_class, svc_config) = prepare_class_load(config, global_config)
        service = Service.new(svc_class, svc_config, parent)
        _LOG.info("Created service: %s", service)
        return service

    @classmethod
    def _build_composite_service(cls, config_list: List[dict],
                                 global_config: Optional[dict] = None,
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
            service.register(cls._build_standalone_service(
                config, global_config, service).export())

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Created mix-in service:\n%s", "\n".join(
                f'  "{key}": {val}' for (key, val) in service.export().items()))

        return service

    @classmethod
    def build_service(cls, config: Union[dict, List[dict]], global_config: Optional[dict] = None,
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
                return cls._build_standalone_service(config, global_config)
            config = [config]

        return cls._build_composite_service(config, global_config, parent)

    @staticmethod
    def build_tunables(config: dict, parent: Optional[TunableGroups] = None) -> TunableGroups:
        """
        Create a new collection of tunable parameters.

        Parameters
        ----------
        config : dict
            Python dict of serialized representation of the covariant tunable groups.
        parent : TunableGroups
            An optional collection of tunables to add to the new collection.

        Returns
        -------
        tunables : TunableGroup
            Create a new collection of tunable parameters.
        """
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Build tunables from config:\n%s",
                       json.dumps(config, indent=2))

        if parent is None:
            return TunableGroups(config)

        groups = TunableGroups()
        groups.update(parent)
        groups.update(TunableGroups(config))
        return groups

    def load_environment(self, json_file_name: str, global_config: Optional[dict] = None,
                         tunables: Optional[TunableGroups] = None, service: Optional[Service] = None) -> Environment:
        """
        Load and build new environment from the config file.

        Parameters
        ----------
        json_file_name : str
            The environment JSON configuration file.
        global_config : dict
            Global parameters to add to the environment config.
        tunables : TunableGroups
            An optional collection of tunables to add to the environment.
        service : Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        env : Environment
            A new benchmarking environment.
        """
        config = self.load_config(json_file_name)
        assert isinstance(config, dict)
        return self.build_environment(config, global_config, tunables, service)

    def load_environment_list(
            self, json_file_name: str, global_config: Optional[dict] = None,
            tunables: Optional[TunableGroups] = None, service: Optional[Service] = None) -> List[Environment]:
        """
        Load and build a list of environments from the config file.

        Parameters
        ----------
        json_file_name : str
            The environment JSON configuration file.
            Can contain either one environment or a list of environments.
        global_config : dict
            Global parameters to add to the environment config.
        tunables : TunableGroups
            An optional collection of tunables to add to the environment.
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
            self.build_environment(config, global_config, tunables, service)
            for config in config_list
        ]

    def load_services(self, json_file_names: List[str],
                      global_config: Optional[dict] = None, parent: Optional[Service] = None) -> Service:
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
        _LOG.info("Load services: %s parent: %s", json_file_names, parent.__class__.__name__)
        service = Service(global_config, parent)
        for fname in json_file_names:
            config = self.load_config(fname)
            service.register(
                ConfigPersistenceService.build_service(config, global_config, service).export())
        return service

    def load_tunables(self, json_file_names: List[str],
                      parent: Optional[TunableGroups] = None) -> TunableGroups:
        """
        Load a collection of tunable parameters from JSON files.

        Parameters
        ----------
        json_file_names : list of str
            A list of JSON files to load.
        parent : TunableGroups
            An optional collection of tunables to add to the new collection.

        Returns
        -------
        tunables : TunableGroup
            Create a new collection of tunable parameters.
        """
        _LOG.info("Load tunables: '%s'", json_file_names)
        groups = TunableGroups()
        if parent is not None:
            groups.update(parent)
        for fname in json_file_names:
            config = self.load_config(fname)
            assert isinstance(config, dict)
            groups.update(TunableGroups(config))
        return groups
