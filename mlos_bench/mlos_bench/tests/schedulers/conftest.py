#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Pytest fixtures for mlos_bench.schedulers tests.
"""
# pylint: disable=redefined-outer-name

import json

import pytest

from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.schedulers.trial_runner import TrialRunner
from mlos_bench.tunables.tunable_groups import TunableGroups
import mlos_bench.tests.optimizers.fixtures as optimizers_fixtures


NUM_TRIAL_RUNNERS = 4


@pytest.fixture
def mock_env_config() -> dict:
    """A config for a MockEnv with mock_trial_data."""
    return {
        "name": "Test MockEnv With Explicit Mock Trial Data",
        "class": "mlos_bench.environments.mock_env.MockEnv",
        "config": {
            "mock_env_seed": -1,
            "mock_env_range": [0, 10],
            "mock_env_metrics": ["score"],
            # TODO: Add more mock trial data here:
            "mock_trial_data": {
                "0": {
                    "setup": {
                        "status": "SUCCEEDED",
                    },
                    "run": {
                        "status": "SUCCEEDED",
                        "metrics": {
                            "score": 1.0,
                        },
                    },
                },
                "1": {
                    "setup": {
                        "status": "SUCCEEDED",
                    },
                    "run": {
                        "status": "SUCCEEDED",
                        "metrics": {
                            "score": 2.0,
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
) -> MockEnv:
    """A fixture to create a MockEnv instance using the mock_env_json_config."""
    config_loader_service = ConfigPersistenceService()
    mock_env = config_loader_service.load_environment(
        mock_env_json_config,
        tunable_groups,
        service=config_loader_service,
    )
    assert isinstance(mock_env, MockEnv)
    return mock_env


@pytest.fixture
def trial_runners(
    mock_env_json_config: str,
    tunable_groups: TunableGroups,
) -> list[TrialRunner]:
    """A fixture to create a list of TrialRunner instances using the
    mock_env_json_config."""
    config_loader_service = ConfigPersistenceService()
    return TrialRunner.create_from_json(
        config_loader=config_loader_service,
        env_json=mock_env_json_config,
        tunable_groups=tunable_groups,
        num_trial_runners=NUM_TRIAL_RUNNERS,
    )
