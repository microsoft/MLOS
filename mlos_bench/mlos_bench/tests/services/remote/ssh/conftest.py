#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Fixtures for the SSH service tests."""

import mlos_bench.tests.services.remote.ssh.fixtures as ssh_fixtures

# Expose some of those as local names so they can be picked up as fixtures by pytest.
ssh_test_server_hostname = ssh_fixtures.ssh_test_server_hostname
ssh_test_server = ssh_fixtures.ssh_test_server
alt_test_server = ssh_fixtures.alt_test_server
reboot_test_server = ssh_fixtures.reboot_test_server
ssh_host_service = ssh_fixtures.ssh_host_service
ssh_fileshare_service = ssh_fixtures.ssh_fileshare_service
