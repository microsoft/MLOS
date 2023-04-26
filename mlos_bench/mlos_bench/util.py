#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Various helper functions for mlos_bench.
"""

# NOTE: This has to be placed in the top-level mlos_bench package to avoid circular imports.

import os
import json
import logging
import importlib
import subprocess
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Union

_LOG = logging.getLogger(__name__)

if TYPE_CHECKING:
    from mlos_bench.environments.base_environment import Environment
    from mlos_bench.optimizers.base_optimizer import Optimizer
    from mlos_bench.services.base_service import Service
    from mlos_bench.storage.base_storage import Storage

# BaseTypeVar is a generic with a constraint of the three base classes.
BaseTypeVar = TypeVar("BaseTypeVar", "Environment", "Optimizer", "Service", "Storage")
BaseTypes = Union["Environment", "Optimizer", "Service", "Storage"]


def prepare_class_load(config: dict,
                       global_config: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
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

    if global_config is None:
        global_config = {}

    for key in set(class_config).intersection(global_config):
        class_config[key] = global_config[key]

    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug("Instantiating: %s with config:\n%s",
                   class_name, json.dumps(class_config, indent=2))

    return (class_name, class_config)


# FIXME: Technically, this should return a type "class_name" derived from "base_class".
def instantiate_from_config(base_class: Type[BaseTypeVar], class_name: str,
                            *args: Any, **kwargs: Any) -> BaseTypeVar:
    """
    Factory method for a new class instantiated from config.

    Parameters
    ----------
    base_class : type
        Base type of the class to instantiate.
        Currently it's one of {Environment, Service, Optimizer}.
    class_name : str
        FQN of a Python class to instantiate, e.g.,
        "mlos_bench.environments.remote.VMEnv".
        Must be derived from the `base_class`.
    args : list
        Positional arguments to pass to the constructor.
    kwargs : dict
        Keyword arguments to pass to the constructor.

    Returns
    -------
    inst : Union[Environment, Service, Optimizer, Storage]
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
    ret: BaseTypeVar = impl(*args, **kwargs)
    assert isinstance(ret, base_class)
    return ret


def check_required_params(config: Mapping[str, Any], required_params: Iterable[str]) -> None:
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


def get_git_info(path: str = __file__) -> Tuple[str, str, str]:
    """
    Get the git repository, commit hash, and local path of the given file.

    Parameters
    ----------
    path : str
        Path to the file in git repository.

    Returns
    -------
    (git_repo, git_commit, git_path) : Tuple[str, str, str]
        Git repository URL, last commit hash, and relative file path.
    """
    dirname = os.path.dirname(path)
    git_repo = subprocess.check_output(
        ["git", "-C", dirname, "remote", "get-url", "origin"], text=True).strip()
    git_commit = subprocess.check_output(
        ["git", "-C", dirname, "rev-parse", "HEAD"], text=True).strip()
    git_root = subprocess.check_output(
        ["git", "-C", dirname, "rev-parse", "--show-toplevel"], text=True).strip()
    _LOG.debug("Current git branch: %s %s", git_repo, git_commit)
    rel_path = os.path.relpath(os.path.abspath(path), os.path.abspath(git_root))
    return (git_repo, git_commit, rel_path.replace("\\", "/"))
