#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Fixtures for the RemoteEnv tests using SSH Services."""

import mlos_bench.tests.docker_fixtures_util as docker_fixtures_util
import mlos_bench.tests.services.remote.ssh.fixtures as ssh_fixtures

# Expose some of those as local names so they can be picked up as fixtures by pytest.
docker_compose_file = ssh_fixtures.docker_compose_file
docker_compose_project_name = ssh_fixtures.docker_compose_project_name

docker_setup = docker_fixtures_util.docker_setup
docker_services_lock = docker_fixtures_util.docker_services_lock
docker_setup_teardown_lock = docker_fixtures_util.docker_setup_teardown_lock
locked_docker_services = docker_fixtures_util.locked_docker_services

ssh_test_server = ssh_fixtures.ssh_test_server
