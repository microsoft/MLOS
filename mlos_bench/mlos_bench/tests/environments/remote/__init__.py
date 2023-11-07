#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helpers for RemoteEnv tests.
"""

from typing import Any, Dict, List, Tuple

from mlos_bench.environments.remote.remote_env import RemoteEnv
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService
from mlos_bench.services.remote.ssh.ssh_fileshare import SshFileShareService
from mlos_bench.tunables.tunable_groups import TunableGroups


def create_remote_ssh_env(tunable_groups: TunableGroups, config: Dict[str, Any]) -> RemoteEnv:
    """
    Create a RemoteEnv with the given configuration that uses SshServices.

    Parameters
    ----------
    tunable_groups : TunableGroups
        Tunable parameters (usually come from a fixture).
    config : Dict[str, Any]
        Environment configuration.

    Returns
    -------
    env : RemoteEnv
        A new instance of the local environment.
    """
    service = ConfigPersistenceService()
    service.register(SshHostService().export())
    service.register(SshFileShareService().export())

    return RemoteEnv(name="TestRemoveEnv", config=config, tunables=tunable_groups, service=service)
