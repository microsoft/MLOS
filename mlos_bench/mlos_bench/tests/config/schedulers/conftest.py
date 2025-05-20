#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Pytest fixtures for Scheduler config tests.

Provides fixtures for creating multiple TrialRunner instances using the mock environment
config.
"""

from importlib.resources import files

import pytest

from mlos_bench.schedulers.trial_runner import TrialRunner
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.util import path_join

# pylint: disable=redefined-outer-name

TRIAL_RUNNERS_COUNT = 4


@pytest.fixture
def mock_env_config_path() -> str:
    """
    Returns the absolute path to the mock environment configuration file.

    This file is used to create TrialRunner instances for testing.
    """
    # Use the files() routine to locate the file relative to this directory
    return path_join(
        str(files("mlos_bench.config").joinpath("environments", "mock", "mock_env.jsonc")),
        abs_path=True,
    )


@pytest.fixture
def trial_runners(
    config_loader_service: ConfigPersistenceService,
    mock_env_config_path: str,
) -> list[TrialRunner]:
    """
    Fixture that returns a list of TrialRunner instances using the mock environment
    config.

    Returns
    -------
    list[TrialRunner]
        List of TrialRunner instances created from the mock environment config.
    """
    return TrialRunner.create_from_json(
        config_loader=config_loader_service,
        env_json=mock_env_config_path,
        num_trial_runners=TRIAL_RUNNERS_COUNT,
    )
