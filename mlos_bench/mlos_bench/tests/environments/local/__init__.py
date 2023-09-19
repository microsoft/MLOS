#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.environments.local.
Used to make mypy happy about multiple conftest.py modules.
"""
from datetime import datetime
from typing import Any, Dict, List, Tuple

import pytest

from mlos_bench.environments.base_environment import Environment
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
    return LocalEnv(name="TestLocalEnv", config=config, tunables=tunable_groups,
                    service=LocalExecService(parent=ConfigPersistenceService()))


def create_composite_local_env(tunable_groups: TunableGroups,
                               params: Dict[str, Any],
                               local_configs: List[Dict[str, Any]]) -> CompositeEnv:
    """
    Create a CompositeEnv with several LocalEnv instances.

    Parameters
    ----------
    tunable_groups : TunableGroups
        Tunable parameters (usually come from a fixture).
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
            ]
        },
        tunables=tunable_groups,
        service=LocalExecService(parent=ConfigPersistenceService()),
    )


def check_env_success(env: Environment,
                      tunable_groups: TunableGroups,
                      expected_results: Dict[str, float],
                      expected_telemetry: List[Tuple[datetime, str, Any]]) -> None:
    """
    Set up a local environment and run a test experiment there.

    Parameters
    ----------
    tunable_groups : TunableGroups
        Tunable parameters (usually come from a fixture).
    env : Environment
        An environment to query for the results.
    expected_results : Dict[str, float]
        Expected results of the benchmark.
    expected_telemetry : List[Tuple[datetime, str, Any]]
        Expected telemetry data of the benchmark.
    """
    with env as env_context:

        assert env_context.setup(tunable_groups)

        (status, data) = env_context.run()
        assert status.is_succeeded()
        assert data == pytest.approx(expected_results, nan_ok=True)

        (status, telemetry) = env_context.status()
        assert status.is_good()
        assert telemetry == pytest.approx(expected_telemetry, nan_ok=True)


def check_env_fail_telemetry(env: Environment, tunable_groups: TunableGroups) -> None:
    """
    Set up a local environment and run a test experiment there;
    Make sure the environment `.status()` call fails.

    Parameters
    ----------
    tunable_groups : TunableGroups
        Tunable parameters (usually come from a fixture).
    env : Environment
        An environment to query for the results.
    """
    with env as env_context:

        assert env_context.setup(tunable_groups)
        (status, _data) = env_context.run()
        assert status.is_succeeded()

        with pytest.raises(ValueError):
            env_context.status()
