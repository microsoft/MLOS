#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for RemoveEnv benchmark environment via local SSH test services."""

import os
import sys
from typing import Dict

import numpy as np
import pytest

from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.tests import requires_docker
from mlos_bench.tests.environments import check_env_success
from mlos_bench.tests.services.remote.ssh import SshTestServerInfo
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files


@requires_docker
def test_remote_ssh_env(ssh_test_server: SshTestServerInfo) -> None:
    """Produce benchmark and telemetry data in a local script and read it."""
    global_config: Dict[str, TunableValue] = {
        "ssh_hostname": ssh_test_server.hostname,
        "ssh_port": ssh_test_server.get_port(),
        "ssh_username": ssh_test_server.username,
        "ssh_priv_key_path": ssh_test_server.id_rsa_path,
    }

    service = ConfigPersistenceService(
        config={"config_path": [str(files("mlos_bench.tests.config"))]}
    )
    config_path = service.resolve_path("environments/remote/test_ssh_env.jsonc")
    env = service.load_environment(
        config_path,
        TunableGroups(),
        global_config=global_config,
        service=service,
    )

    check_env_success(
        env,
        env.tunable_params,
        expected_results={
            "hostname": ssh_test_server.service_name,
            "username": ssh_test_server.username,
            "score": 0.9,
            "ssh_priv_key_path": np.nan,  # empty strings are returned as "not a number"
            "test_param": "unset",
            "FOO": "unset",
            "ssh_username": "unset",
        },
        expected_telemetry=[],
    )
    assert not os.path.exists(
        os.path.join(os.getcwd(), "output-downloaded.csv")
    ), "output-downloaded.csv should have been cleaned up by temp_dir context"


if __name__ == "__main__":
    pytest.main(["-n1", __file__])
