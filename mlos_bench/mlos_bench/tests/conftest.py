#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Common fixtures for mock TunableGroups and Environment objects."""

import sys

import pytest

from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.tests import SEED, resolve_host_name, tunable_groups_fixtures
from mlos_bench.tunables.tunable_groups import TunableGroups

# pylint: disable=redefined-outer-name
# -- Ignore pylint complaints about pytest references to
# `tunable_groups` fixture as both a function and a parameter.

# Expose some of those as local names so they can be picked up as fixtures by pytest.
tunable_groups_config = tunable_groups_fixtures.tunable_groups_config
tunable_groups = tunable_groups_fixtures.tunable_groups
mixed_numerics_tunable_groups = tunable_groups_fixtures.mixed_numerics_tunable_groups
covariant_group = tunable_groups_fixtures.covariant_group


HOST_DOCKER_NAME = "host.docker.internal"


@pytest.fixture(scope="session")
def docker_hostname() -> str:
    """Returns the local hostname to use to connect to the test ssh server."""
    if sys.platform != "win32" and resolve_host_name(HOST_DOCKER_NAME):
        # On Linux, if we're running in a docker container, we can use the
        # --add-host (extra_hosts in docker-compose.yml) to refer to the host IP.
        return HOST_DOCKER_NAME
    # Docker (Desktop) for Windows (WSL2) uses a special networking magic
    # to refer to the host machine as `localhost` when exposing ports.
    # In all other cases, assume we're executing directly inside conda on the host.
    return "127.0.0.1"  # "localhost"


@pytest.fixture
def mock_env(tunable_groups: TunableGroups) -> MockEnv:
    """Test fixture for MockEnv."""
    return MockEnv(
        name="Test Env",
        config={
            "tunable_params": ["provision", "boot", "kernel"],
            "mock_env_seed": SEED,
            "mock_env_range": [60, 120],
            "mock_env_metrics": ["score"],
        },
        tunables=tunable_groups,
    )


@pytest.fixture
def mock_env_no_noise(tunable_groups: TunableGroups) -> MockEnv:
    """Test fixture for MockEnv."""
    return MockEnv(
        name="Test Env No Noise",
        config={
            "tunable_params": ["provision", "boot", "kernel"],
            "mock_env_seed": -1,
            "mock_env_range": [60, 120],
            "mock_env_metrics": ["score", "other_score"],
        },
        tunables=tunable_groups,
    )
