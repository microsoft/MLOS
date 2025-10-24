#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Fixtures for the SSH service tests."""

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
alt_test_server = ssh_fixtures.alt_test_server
reboot_test_server = ssh_fixtures.reboot_test_server
ssh_host_service = ssh_fixtures.ssh_host_service
ssh_fileshare_service = ssh_fixtures.ssh_fileshare_service
