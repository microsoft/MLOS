"""
Benchmarking environments for OS Autotune.
"""

from typing import Any, Dict, Iterable

from mlos_bench.environment.status import Status
from mlos_bench.environment.tunable import Tunable, TunableGroups
from mlos_bench.environment.base_service import Service
from mlos_bench.environment.base_environment import Environment
from mlos_bench.environment.base_fileshare import FileShareService

from mlos_bench.environment.app import AppEnv
from mlos_bench.environment.composite import CompositeEnv
from mlos_bench.environment.config_persistence import ConfigPersistenceService


def _check_required_params(config: Dict[str, Any], required_params: Iterable[str]):
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
            "The following parameters must be provided "
            "in the configuration or as command line arguments: "
            + str(missing_params))


__all__ = [
    'Status',
    'Tunable',
    'TunableGroups',
    'Service',
    'Environment',
    'AppEnv',
    'CompositeEnv',
    'ConfigPersistenceService',
    'FileShareService',
]
