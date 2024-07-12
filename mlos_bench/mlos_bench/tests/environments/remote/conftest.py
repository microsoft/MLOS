#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Fixtures for the RemoteEnv tests using SSH Services."""

import mlos_bench.tests.services.remote.ssh.fixtures as ssh_fixtures

# Expose some of those as local names so they can be picked up as fixtures by pytest.
ssh_test_server = ssh_fixtures.ssh_test_server
ssh_test_server_hostname = ssh_fixtures.ssh_test_server_hostname
