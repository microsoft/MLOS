#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Common fixtures for mock TunableGroups and Environment objects."""

import os
from typing import Any, Generator, List

import pytest
from fasteners import InterProcessLock, InterProcessReaderWriterLock
from pytest_docker.plugin import Services as DockerServices
from pytest_docker.plugin import get_docker_services

from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.tests import SEED, tunable_groups_fixtures
from mlos_bench.tunables.tunable_groups import TunableGroups

# pylint: disable=redefined-outer-name
# -- Ignore pylint complaints about pytest references to
# `tunable_groups` fixture as both a function and a parameter.

# Expose some of those as local names so they can be picked up as fixtures by pytest.
tunable_groups_config = tunable_groups_fixtures.tunable_groups_config
tunable_groups = tunable_groups_fixtures.tunable_groups
mixed_numerics_tunable_groups = tunable_groups_fixtures.mixed_numerics_tunable_groups
covariant_group = tunable_groups_fixtures.covariant_group


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


# Fixtures to configure the pytest-docker plugin.


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig: pytest.Config) -> List[str]:
    """
    Returns the path to the docker-compose file.

    Parameters
    ----------
    pytestconfig : pytest.Config

    Returns
    -------
    str
        Path to the docker-compose file.
    """
    _ = pytestconfig  # unused
    return [
        os.path.join(os.path.dirname(__file__), "services", "remote", "ssh", "docker-compose.yml"),
        # Add additional configs as necessary here.
    ]


@pytest.fixture(scope="session")
def docker_compose_project_name(short_testrun_uid: str) -> str:
    """
    Returns the name of the docker-compose project.

    Returns
    -------
    str
        Name of the docker-compose project.
    """
    # Use the xdist testrun UID to ensure that the docker-compose project name
    # is unique across sessions, but shared amongst workers.
    return f"mlos_bench-test-{short_testrun_uid}"


@pytest.fixture(scope="session")
def docker_services_lock(
    shared_temp_dir: str,
    short_testrun_uid: str,
) -> InterProcessReaderWriterLock:
    """
    Gets a pytest session lock for xdist workers to mark when they're using the docker
    services.

    Yields
    ------
        A lock to ensure that setup/teardown operations don't happen while a
        worker is using the docker services.
    """
    return InterProcessReaderWriterLock(
        f"{shared_temp_dir}/pytest_docker_services-{short_testrun_uid}.lock"
    )


@pytest.fixture(scope="session")
def docker_setup_teardown_lock(shared_temp_dir: str, short_testrun_uid: str) -> InterProcessLock:
    """
    Gets a pytest session lock between xdist workers for the docker setup/teardown
    operations.

    Yields
    ------
        A lock to ensure that only one worker is doing setup/teardown at a time.
    """
    return InterProcessLock(
        f"{shared_temp_dir}/pytest_docker_services-setup-teardown-{short_testrun_uid}.lock"
    )


@pytest.fixture(scope="session")
def locked_docker_services(
    docker_compose_command: Any,
    docker_compose_file: Any,
    docker_compose_project_name: Any,
    docker_setup: Any,
    docker_cleanup: Any,
    docker_setup_teardown_lock: InterProcessLock,
    docker_services_lock: InterProcessReaderWriterLock,
) -> Generator[DockerServices, Any, None]:
    """A locked version of the docker_services fixture to implement xdist single
    instance locking.
    """
    # pylint: disable=too-many-arguments
    # Mark the services as in use with the reader lock.
    docker_services_lock.acquire_read_lock()
    # Acquire the setup lock to prevent multiple setup operations at once.
    docker_setup_teardown_lock.acquire()
    # This "with get_docker_services(...)"" pattern is in the default fixture.
    # We call it instead of docker_services() to avoid pytest complaints about
    # calling fixtures directly.
    with get_docker_services(
        docker_compose_command,
        docker_compose_file,
        docker_compose_project_name,
        docker_setup,
        docker_cleanup,
    ) as docker_services:
        # Release the setup/tear down lock in order to let the setup operation
        # continue for other workers (should be a no-op at this point).
        docker_setup_teardown_lock.release()
        # Yield the services so that tests within this worker can use them.
        yield docker_services
        # Now tests that use those services get to run on this worker...
        # Once the tests are done, release the read lock that marks the services as in use.
        docker_services_lock.release_read_lock()
        # Now as we prepare to execute the cleanup code on context exit we need
        # to acquire the setup/teardown lock again.
        # First we attempt to get the write lock so that we wait for other
        # readers to finish and guard against a lock inversion possibility.
        docker_services_lock.acquire_write_lock()
        # Next, acquire the setup/teardown lock
        # First one here is the one to do actual work, everyone else is basically a no-op.
        # Upon context exit, we should execute the docker_cleanup code.
        # And try to get the setup/tear down lock again.
        docker_setup_teardown_lock.acquire()
    # Finally, after the docker_cleanup code has finished, remove both locks.
    docker_setup_teardown_lock.release()
    docker_services_lock.release_write_lock()
