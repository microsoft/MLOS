#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Pytest fixtures for mlos_bench.schedulers tests."""
# pylint: disable=redefined-outer-name

import json

import pytest

from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.schedulers.trial_runner import TrialRunner
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.tunables.tunable_groups import TunableGroups

NUM_TRIAL_RUNNERS = 4


@pytest.fixture
def mock_env_config() -> dict:
    """A config for a MockEnv with mock_trial_data."""
    return {
        "name": "Test MockEnv With Explicit Mock Trial Data",
        "class": "mlos_bench.environments.mock_env.MockEnv",
        "config": {
            # Reference the covariant groups from the `tunable_groups` fixture.
            # See Also:
            # - mlos_bench/tests/conftest.py
            # - mlos_bench/tests/tunable_groups_fixtures.py
            "tunable_params": ["provision", "boot", "kernel"],
            "mock_env_seed": -1,
            "mock_env_range": [0, 10],
            "mock_env_metrics": ["score"],
            # TODO: Add more mock trial data here:
            "mock_trial_data": {
                "1": {
                    "run": {
                        "sleep": 0.25,
                        "status": "SUCCEEDED",
                        "metrics": {
                            "score": 1.0,
                        },
                    },
                },
                "2": {
                    "run": {
                        "sleep": 0.3,
                        "status": "SUCCEEDED",
                        "metrics": {
                            "score": 2.0,
                        },
                    },
                },
                "3": {
                    "run": {
                        "sleep": 0.2,
                        "status": "SUCCEEDED",
                        "metrics": {
                            "score": 3.0,
                        },
                    },
                },
            },
        },
    }


@pytest.fixture
def mock_env_json_config(mock_env_config: dict) -> str:
    """A JSON string of the mock_env_config."""
    return json.dumps(mock_env_config)


@pytest.fixture
def mock_env(
    mock_env_json_config: str,
    tunable_groups: TunableGroups,
    mock_env_global_config: dict,
) -> MockEnv:
    """A fixture to create a MockEnv instance using the mock_env_json_config."""
    config_loader_service = ConfigPersistenceService()
    mock_env = config_loader_service.load_environment(
        mock_env_json_config,
        tunable_groups,
        service=config_loader_service,
        global_config=mock_env_global_config,
    )
    assert isinstance(mock_env, MockEnv)
    return mock_env


@pytest.fixture
def trial_runners(
    mock_env_json_config: str,
    tunable_groups: TunableGroups,
    mock_env_global_config: dict,
) -> list[TrialRunner]:
    """A fixture to create a list of TrialRunner instances using the
    mock_env_json_config.
    """
    config_loader_service = ConfigPersistenceService(
        global_config=mock_env_global_config,
    )
    return TrialRunner.create_from_json(
        config_loader=config_loader_service,
        env_json=mock_env_json_config,
        tunable_groups=tunable_groups,
        num_trial_runners=NUM_TRIAL_RUNNERS,
        global_config=mock_env_global_config,
    )
