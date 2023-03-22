#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Various helper functions for mlos_bench.
"""

# NOTE: This has to be placed in the top-level mlos_bench package to avoid circular imports.

import json
import logging
import importlib
from typing import Any, Tuple, Dict, Iterable

_LOG = logging.getLogger(__name__)


def prepare_class_load(config: dict, global_config: dict = None) -> Tuple[str, Dict[str, Any]]:
    """
    Extract the class instantiation parameters from the configuration.

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

    for key in set(class_config).intersection(global_config or {}):
        class_config[key] = global_config[key]

    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug("Instantiating: %s with config:\n%s",
                   class_name, json.dumps(class_config, indent=2))

    return (class_name, class_config)


def instantiate_from_config(base_class: type, class_name: str, *args, **kwargs):
    """
    Factory method for a new class instantiated from config.

    Parameters
    ----------
    base_class : type
        Base type of the class to instantiate.
        Currently it's one of {Environment, Service, Optimizer}.
    class_name : str
        FQN of a Python class to instantiate, e.g.,
        "mlos_bench.environment.remote.HostEnv".
        Must be derived from the `base_class`.
    args : list
        Positional arguments to pass to the constructor.
    kwargs : dict
        Keyword arguments to pass to the constructor.

    Returns
    -------
    inst : Any
        An instance of the `class_name` class.
    """
    # We need to import mlos_bench to make the factory methods work.
    class_name_split = class_name.split(".")
    module_name = ".".join(class_name_split[:-1])
    class_id = class_name_split[-1]

    module = importlib.import_module(module_name)
    impl = getattr(module, class_id)
    _LOG.info("Instantiating: %s :: %s", class_name, impl)

    assert issubclass(impl, base_class)
    return impl(*args, **kwargs)


def check_required_params(config: Dict[str, Any], required_params: Iterable[str]):
    """
    Check if all required parameters are present in the configuration.
    Raise ValueError if any of the parameters are missing.

    Parameters
    ----------
    config : dict
        Free-format dictionary with the configuration
        of the service or benchmarking environment.
    required_params : Iterable[str]
        A collection of identifiers of the parameters that must be present
        in the configuration.
    """
    missing_params = set(required_params).difference(config)
    if missing_params:
        raise ValueError(
            "The following parameters must be provided in the configuration"
            + f" or as command line arguments: {missing_params}")
