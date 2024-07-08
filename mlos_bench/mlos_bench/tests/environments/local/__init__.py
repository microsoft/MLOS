#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.environments.local.

Used to make mypy happy about multiple conftest.py modules.
"""

from typing import Any, Dict, List

from mlos_bench.environments.composite_env import CompositeEnv
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
    env : LocalEnv
        A new instance of the local environment.
    """
    return LocalEnv(
        name="TestLocalEnv",
        config=config,
        tunables=tunable_groups,
        service=LocalExecService(parent=ConfigPersistenceService()),
    )


def create_composite_local_env(
    tunable_groups: TunableGroups,
    global_config: Dict[str, Any],
    params: Dict[str, Any],
    local_configs: List[Dict[str, Any]],
) -> CompositeEnv:
    """
    Create a CompositeEnv with several LocalEnv instances.

    Parameters
    ----------
    tunable_groups : TunableGroups
        Tunable parameters (usually come from a fixture).
    global_config : Dict[str, Any]
        Global configuration parameters.
    params: Dict[str, Any]
        Additional config params for the CompositeEnv.
    local_configs: List[Dict[str, Any]]
        Configurations of the local environments.

    Returns
    -------
    env : CompositeEnv
        A new instance of the local environment.
    """
    return CompositeEnv(
        name="TestCompositeEnv",
        config={
            **params,
            "children": [
                {
                    "name": f"TestLocalEnv{i}",
                    "class": "mlos_bench.environments.local.local_env.LocalEnv",
                    "config": config,
                }
                for (i, config) in enumerate(local_configs)
            ],
        },
        tunables=tunable_groups,
        global_config=global_config,
        service=LocalExecService(parent=ConfigPersistenceService()),
    )
