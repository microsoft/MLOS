#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for loading environment config examples.
"""

from typing import List

import logging
import os

import pytest

from mlos_bench.tests.config import locate_config_examples
from mlos_bench.environments.base_environment import Environment
from mlos_bench.services.config_persistence import ConfigPersistenceService


_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


# Get the set of configs to test.
CONFIG_TYPE = "environments"


def filter_configs(configs_to_filter: List[str]) -> List[str]:
    """If necessary, filter out json files that aren't for the module we're testing."""
    for config_path in configs_to_filter:
        if config_path.endswith("-tunables.jsonc"):
            configs_to_filter.remove(config_path)
    return configs_to_filter


configs = filter_configs(locate_config_examples(os.path.join(ConfigPersistenceService.BUILTIN_CONFIG_PATH, CONFIG_TYPE)))
assert configs


@pytest.mark.parametrize("config_path", configs)
def test_load_environment_config_examples(config_loader_service: ConfigPersistenceService, config_path: str) -> None:
    """Tests loading a config example."""
    global_config = {
        "experimentId": "test",
        "trialId": 1,
    }

    mock_service_configs = [
        "services/remote/mock/mock_vm_service.jsonc",
        "services/local/mock/mock_local_exec_service.jsonc",
    ]

    for mock_service_config_path in mock_service_configs:
        mock_service_config = config_loader_service.load_config(mock_service_config_path)
        config_loader_service.register(config_loader_service.build_service(
                                       config=mock_service_config,
                                       parent=config_loader_service,
                                      ).export())

    envs = config_loader_service.load_environment_list(config_path, global_config, service=config_loader_service)
    for env in envs:
        assert env is not None
        assert isinstance(env, Environment)
