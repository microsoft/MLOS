#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helper functions for various docker test fixtures.

Test functions needing to use these should import them and then add them to their
namespace in a conftest.py file.

The intent of keeping these separate from conftest.py is to allow individual test to
setup their own docker-compose configurations that are independent.

As such, each conftest.py should set their own docker_compose_file fixture pointing to
the appropriate docker-compose.yml file(s) and set a unique docker_compose_project_name.
"""
# pylint: disable=redefined-outer-name

import os
import sys
from collections.abc import Generator
from typing import Any

import pytest
from fasteners import InterProcessLock, InterProcessReaderWriterLock
from pytest_docker.plugin import Services as DockerServices
from pytest_docker.plugin import get_docker_services


# Fixtures to configure the pytest-docker plugin.
@pytest.fixture(scope="session")
def docker_setup() -> list[str] | str:
    """Setup for docker services."""
    if sys.platform == "darwin" or os.environ.get("HOST_OSTYPE", "").lower().startswith("darwin"):
        # Workaround an oddity on macOS where the "docker-compose up"
        # command always recreates the containers.
        # That leads to races when multiple workers are trying to
        # start and use the same services.
        return ["up --build -d --no-recreate"]
    else:
        return ["up --build -d"]


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig: pytest.Config) -> list[str]:
    """
    Fixture for the path to the docker-compose file.

    Parameters
    ----------
    pytestconfig : pytest.Config

    Returns
    -------
    list[str]
        List of paths to the docker-compose file(s).
    """
    _ = pytestconfig  # unused
    # Add additional configs as necessary here.
    # return []
    raise NotImplementedError("Please implement docker_compose_file in your conftest.py")


@pytest.fixture(scope="session")
def docker_compose_project_name(short_testrun_uid: str) -> str:
    """
    Fixture for the name of the docker-compose project.

    Returns
    -------
    str
        Name of the docker-compose project.
    """
    # Use the xdist testrun UID to ensure that the docker-compose project name
    # is unique across sessions, but shared amongst workers.
    # return f"""mlos_bench-test-{short_testrun_uid}-{__name__.replace(".", "-")}"""
    raise NotImplementedError("Please implement docker_compose_project_name in your conftest.py")


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
    # pylint: disable=too-many-arguments,too-many-positional-arguments
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


__all__ = [
    # These two should be implemented in the conftest.py of the local test suite
    # "docker_compose_file",
    # "docker_compose_project_name",
    "docker_setup",
    "docker_services_lock",
    "docker_setup_teardown_lock",
    "locked_docker_services",
]
