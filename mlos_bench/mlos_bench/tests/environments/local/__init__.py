#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.environments.local.
Used to make mypy happy about multiple conftest.py modules.
"""
from typing import Any, Dict

from mlos_bench.environments.local.local_env import LocalEnv
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.tunables.tunable_groups import TunableGroups


def create_local_env(tunable_groups: TunableGroups, config: Dict[str, Any]) -> LocalEnv:
    """
    Create a LocalEnv with the given configuration.

    Parameters
    ----------
    tunable_groups : TunableGroups
        Tunable parameters (usually come from a fixture).
    config : Dict[str, Any]
        Environment configuration.

    Returns
    -------
    local_env : LocalEnv
        A new instance of the local environment.
    """
    return LocalEnv(name="TestLocalEnv", config=config, tunables=tunable_groups,
                    service=LocalExecService(parent=ConfigPersistenceService()))
