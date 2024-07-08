#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests helpers for mlos_bench.environments."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pytest

from mlos_bench.environments.base_environment import Environment
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups


def check_env_success(
    env: Environment,
    tunable_groups: TunableGroups,
    expected_results: Dict[str, TunableValue],
    expected_telemetry: List[Tuple[datetime, str, Any]],
    global_config: Optional[dict] = None,
) -> None:
    """
    Set up an environment and run a test experiment there.

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
    global_config : dict
        Global params.
    """
    with env as env_context:

        assert env_context.setup(tunable_groups, global_config)

        (status, _ts, data) = env_context.run()
        assert status.is_succeeded()
        assert data == pytest.approx(expected_results, nan_ok=True)

        (status, _ts, telemetry) = env_context.status()
        assert status.is_good()
        assert telemetry == pytest.approx(expected_telemetry, nan_ok=True)

        env_context.teardown()
        assert not env_context._is_ready  # pylint: disable=protected-access


def check_env_fail_telemetry(env: Environment, tunable_groups: TunableGroups) -> None:
    """
    Set up a local environment and run a test experiment there; Make sure the
    environment `.status()` call fails.

    Parameters
    ----------
    tunable_groups : TunableGroups
        Tunable parameters (usually come from a fixture).
    env : Environment
        An environment to query for the results.
    """
    with env as env_context:

        assert env_context.setup(tunable_groups)
        (status, _ts, _data) = env_context.run()
        assert status.is_succeeded()

        with pytest.raises(ValueError):
            env_context.status()
