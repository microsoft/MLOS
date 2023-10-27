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


def preprocess_dynamic_configs(*, dest: dict, source: Optional[dict] = None) -> dict:
    """
    Replaces all $name values in the destination config with the corresponding
    value from the source config.

    Parameters
    ----------
    dest : dict
        Destination config.
    source : Optional[dict]
        Source config.

    Returns
    -------
    dest : dict
        A reference to the destination config after the preprocessing.
    """
    if source is None:
        source = {}
    for key, val in dest.items():
        if isinstance(val, str) and val.startswith("$") and val[1:] in source:
            dest[key] = source[val[1:]]
    return dest


def merge_parameters(*, dest: dict, source: Optional[dict] = None,
                     required_keys: Optional[Iterable[str]] = None) -> dict:
    """
    Merge the source config dict into the destination config.
    Pick from the source configs *ONLY* the keys that are already present
    in the destination config.

    Parameters
    ----------
    dest : dict
        Destination config.
    source : Optional[dict]
        Source config.
    required_keys : Optional[Iterable[str]]
        An optional list of keys that must be present in the destination config.

    Returns
    -------
    dest : dict
        A reference to the destination config after the merge.
    """
    if source is None:
        source = {}

    for key in set(dest).intersection(source):
        dest[key] = source[key]

    for key in required_keys or []:
        if key in dest:
            continue
        if key in source:
            dest[key] = source[key]
        else:
            raise ValueError("Missing required parameter: " + key)

    return dest


def path_join(*args: str, abs_path: bool = False) -> str:
    """
    Joins the path components and normalizes the path.

    Parameters
    ----------
    args : str
        Path components.

    abs_path : bool
        If True, the path is converted to be absolute.

    Returns
    -------
    str
        Joined path.
    """
    path = os.path.join(*args)
    if abs_path:
        path = os.path.abspath(path)
    return os.path.normpath(path).replace("\\", "/")


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

    merge_parameters(dest=class_config, source=global_config)

    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug("Instantiating: %s with config:\n%s",
                   class_name, json.dumps(class_config, indent=2))

    return (class_name, class_config)


def get_class_from_name(class_name: str) -> type:
    """
    Gets the class from the fully qualified name.

    Parameters
    ----------
    class_name : str
        Fully qualified class name.

    Returns
    -------
    type
        Class object.
    """
    # We need to import mlos_bench to make the factory methods work.
    class_name_split = class_name.split(".")
    module_name = ".".join(class_name_split[:-1])
    class_id = class_name_split[-1]

    module = importlib.import_module(module_name)
    cls = getattr(module, class_id)
    assert isinstance(cls, type)
    return cls


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
        "mlos_bench.environments.remote.HostEnv".
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
    impl = get_class_from_name(class_name)
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


# Note: to avoid circular imports, we don't specify TunableValue here.
def try_parse_val(val: Optional[str]) -> Optional[Union[int, float, str]]:
    """
    Try to parse the value as an int or float, otherwise return the string.

    This can help with config schema validation to make sure early on that
    the args we're expecting are the right type.

    Parameters
    ----------
    val : str
        The initial cmd line arg value.

    Returns
    -------
    TunableValue
        The parsed value.
    """
    if val is None:
        return val
    try:
        val_float = float(val)
        try:
            val_int = int(val)
            return val_int if val_int == val_float else val_float
        except ValueError:
            return val_float
    except ValueError:
        return str(val)
