"""
Helper functions to load, instantiate, and serialize Python objects
that encapsulate benchmark environments, tunable parameters, and
service functions.
"""

import json
import logging
from typing import List

from mlos_bench.environment.tunable import TunableGroups
from mlos_bench.environment.base_service import Service
from mlos_bench.environment.base_environment import Environment

_LOG = logging.getLogger(__name__)


def build_environment(config, global_config=None, tunables=None, service=None):
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
    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug("Build environment from config:\n%s",
                   json.dumps(config, indent=2))

    env_name = config["name"]
    env_class = config["class"]
    env_config = config.get("config", {})

    if global_config:
        local_config = global_config.copy()
        local_config.update(env_config)
        env_config = local_config

    env_services_path = config.get("include_services")
    if env_services_path is not None:
        service = load_services(env_services_path, global_config, service)

    env_tunables_path = config.get("include_tunables")
    if env_tunables_path is not None:
        tunables = load_tunables(env_tunables_path, tunables)

    _LOG.debug("Creating env: %s :: %s", env_name, env_class)
    env = Environment.new(env_name, env_class, env_config, tunables, service)

    _LOG.info("Created env: %s :: %s", env_name, env)
    return env


def _build_standalone_service(config, global_config=None):
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

    Returns
    -------
    svc : Service
        An instance of the `Service` class initialized with `config`.
    """
    svc_class = config["class"]
    svc_config = config.get("config", {})

    if global_config:
        local_config = global_config.copy()
        local_config.update(svc_config)
        svc_config = local_config

    _LOG.debug("Creating service: %s", svc_class)
    service = Service.new(svc_class, svc_config)

    _LOG.info("Created service: %s", service)
    return service


def _build_composite_service(config_list, global_config=None, parent=None):
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
        service.register(_build_standalone_service(config, global_config).export())
    _LOG.info("Created mix-in service: %s", service.export())
    return service


def build_service(config: List[dict], global_config=None, parent=None):
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
            return _build_standalone_service(config, global_config)
        config = [config]

    return _build_composite_service(config, global_config, parent)


def build_tunables(config, parent=None):
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


def load_environment(json_file_name, global_config=None,
                     tunables=None, service=None):
    """
    Create a new collection of tunable parameters.

    Parameters
    ----------
    json_file_name : str
        The environment JSON configuration file.
    global_config : dict
        Global parameters to add to the environment config.
    tunables : TunableGroups
        An optional collection of tunables to add to the new collection.
    service : Service
        An optional reference of the parent service to mix in.
    """
    _LOG.info("Load environment: %s", json_file_name)
    with open(json_file_name, encoding='utf-8') as fh_json:
        config = json.load(fh_json)
        return build_environment(config, global_config, tunables, service)


def load_services(json_file_names: List[str], global_config: dict = None, parent: Service = None):
    """
    Create a new collection of tunable parameters.

    Parameters
    ----------
    json_file_names : list of str
        The service JSON configuration file.
    global_config : dict
        Global parameters to add to the service config.
    parent : Service
        An optional reference of the parent service to mix in.

    Returns
    -------
    tunables : TunableGroup
        Create a new collection of tunable parameters.
    """
    _LOG.info("Load services: %s", json_file_names)
    service = Service(global_config)
    if parent:
        service.register(parent.export())
    for fname in json_file_names:
        _LOG.debug("Load services: %s", fname)
        with open(fname, encoding='utf-8') as fh_json:
            config = json.load(fh_json)
            service.register(build_service(config, global_config).export())
    return service


def load_tunables(json_file_names: List[str], parent: TunableGroups = None):
    """
    Load a collection of tunable parameters from JSON files.

    Parameters
    ----------
    json_file_names : list of str
        A list of JSON files to load.
    parent : TunableGroups
        An optional collection of tunables to add to the new collection.
    """
    _LOG.info("Load tunables: %s", json_file_names)
    groups = TunableGroups()
    if parent is not None:
        groups.update(parent)
    for fname in json_file_names:
        _LOG.debug("Load tunables: %s", fname)
        with open(fname, encoding='utf-8') as fh_json:
            config = json.load(fh_json)
            groups.update(TunableGroups(config))
    return groups
