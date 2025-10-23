#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests helpers for mlos_bench.environments."""

from datetime import datetime
from typing import Any

import pytest

from mlos_bench.environments.base_environment import Environment
from mlos_bench.environments.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.tunables.tunable_types import TunableValue


def check_env_success(
    env: Environment,
    tunable_groups: TunableGroups,
    *,
    expected_results: dict[str, TunableValue] | None,
    expected_telemetry: list[tuple[datetime, str, Any]],
    expected_status_run: set[Status] | None = None,
    expected_status_next: set[Status] | None = None,
    global_config: dict | None = None,
) -> None:
    """
    Set up an environment and run a test experiment there.

    Parameters
    ----------
    tunable_groups : TunableGroups
        Tunable parameters (usually come from a fixture).
    env : Environment
        An environment to query for the results.
    expected_results : dict[str, float]
        Expected results of the benchmark.
    expected_telemetry : list[tuple[datetime, str, Any]]
        Expected telemetry data of the benchmark.
    expected_status_run : set[Status]
        Expected status right after the trial.
        Default is the `SUCCEEDED` value.
    expected_status_next : set[Status]
        Expected status values for the next trial.
        Default is the same set as in `.is_good()`.
    global_config : dict
        Global params.
    """
    # pylint: disable=too-many-arguments
    if expected_status_run is None:
        expected_status_run = {Status.SUCCEEDED}

    if expected_status_next is None:
        expected_status_next = {
            Status.PENDING,
            Status.READY,
            Status.RUNNING,
            Status.SUCCEEDED,
        }

    with env as env_context:

        assert env_context.setup(tunable_groups, global_config)

        (status, _ts, data) = env_context.run()
        assert status in expected_status_run
        if expected_results is None:
            assert data is None
        else:
            assert data == pytest.approx(expected_results, nan_ok=True)

        (status, _ts, telemetry) = env_context.status()
        assert status in expected_status_next
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
