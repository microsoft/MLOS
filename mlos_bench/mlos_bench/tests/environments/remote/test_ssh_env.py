#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for RemoveEnv benchmark environment via local SSH test services.
"""

from typing import Dict

import os
import sys

import pytest

from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups

from mlos_bench.tests import requires_docker
from mlos_bench.tests.environments import check_env_success
from mlos_bench.tests.services.remote.ssh import SshTestServerInfo

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files


@requires_docker
@pytest.mark.xdist_group("ssh_test_server")
def test_remote_ssh_env(tunable_groups: TunableGroups, ssh_test_server: SshTestServerInfo) -> None:
    """
    Produce benchmark and telemetry data in a local script and read it.
    """
    global_config: Dict[str, TunableValue] = {
        "ssh_hostname": ssh_test_server.hostname,
        "ssh_port": ssh_test_server.get_port(),
        "ssh_username": ssh_test_server.username,
        "ssh_priv_key_path": ssh_test_server.id_rsa_path,
    }

    service = ConfigPersistenceService(config={"config_path": [str(files("mlos_bench.tests.config"))]})
    config_path = service.resolve_path("environments/remote/test_ssh_env.jsonc")
    env = service.load_environment(config_path, tunable_groups, global_config=global_config, service=service)

    check_env_success(
        env, tunable_groups,
        expected_results={
            "hostname": ssh_test_server.service_name,
            "username": ssh_test_server.username,
            "score": 0.9,
        },
        expected_telemetry=[],
    )
    assert not os.path.exists(os.path.join(os.getcwd(), "output-downloaded.csv")), \
        "output-downloaded.csv should have been cleaned up by temp_dir context"


if __name__ == "__main__":
    pytest.main(["-n1", __file__])
