#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for RemoveEnv benchmark environment via local SSH test services.
"""

import sys

from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.tunables.tunable_groups import TunableGroups

from mlos_bench.tests.environments import check_env_success
from mlos_bench.tests.services.remote.ssh import SshTestServerInfo

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files


def test_remote_ssh_env(tunable_groups: TunableGroups, ssh_test_server: SshTestServerInfo) -> None:
    """
    Produce benchmark and telemetry data in a local script and read it.
    """
    global_config = {
        "ssh_hostname": ssh_test_server.hostname,
        "ssh_port": ssh_test_server.get_port(),
        "ssh_username": ssh_test_server.username,
        "ssh_priv_key_path": ssh_test_server.id_rsa_path,
    }

    service = ConfigPersistenceService(config={"config_path": [str(files("mlos_bench.tests.config"))]})
    config_path = service.resolve_path("environments/remote/test_ssh_env.jsonc")
    env = service.load_environment(config_path, tunable_groups, global_config)

    check_env_success(
        env, tunable_groups,
        expected_results={
            "hostname": ssh_test_server.service_name,
            "username": ssh_test_server.username,
            "score": 0.9,
        },
        expected_telemetry=[],
    )
