#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Various helper functions for mlos_bench.
"""

# NOTE: This has to be placed in the top-level mlos_bench package to avoid circular imports.

import logging
import importlib
import subprocess
from typing import Any, Tuple, Dict, Iterable

_LOG = logging.getLogger(__name__)


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
        "mlos_bench.environment.remote.VMEnv".
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


def get_git_info(path: str = ".") -> Tuple[str, str]:
    """
    Get the git repository and commit hash of the current working directory.

    Parameters
    ----------
    path : str
        Path to the git repository.

    Returns
    -------
    (git_repo, git_commit) : Tuple[str, str]
        Git repository URL and last commit hash.
    """
    git_repo = subprocess.check_output(
        ["cd", path, "&&", "git", "remote", "get-url", "origin"],
        shell=True, text=True).strip()
    git_commit = subprocess.check_output(
        ["cd", path, "&&", "git", "rev-parse", "HEAD"],
        shell=True, text=True).strip()
    _LOG.debug("Current git branch: %s %s", git_repo, git_commit)
    return (git_repo, git_commit)
