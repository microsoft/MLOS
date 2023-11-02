#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Fixtures for the RemoteEnv tests using SSH Services.
"""

import mlos_bench.tests.services.remote.ssh.fixtures as ssh_fixtures

# Expose those as local names.
ssh_test_server_hostname = ssh_fixtures.ssh_test_server_hostname
ssh_test_server = ssh_fixtures.ssh_test_server
ssh_host_service = ssh_fixtures.ssh_host_service
ssh_fileshare_service = ssh_fixtures.ssh_fileshare_service
