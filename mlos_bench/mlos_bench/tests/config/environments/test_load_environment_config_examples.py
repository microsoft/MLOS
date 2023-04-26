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
    return configs_to_filter


configs = filter_configs(locate_config_examples(os.path.join(ConfigPersistenceService.BUILTIN_CONFIG_PATH, CONFIG_TYPE)))
assert configs


@pytest.mark.parametrize("config_path", configs)
def test_load_environment_config_examples(config_loader_service: ConfigPersistenceService, config_path: str) -> None:
    """Tests loading a config example."""
    config = config_loader_service.load_config(config_path)
    assert isinstance(config, dict)
    # Make an instance of the class based on the config.
    env_inst = config_loader_service.build_environment(
        config=config,
        service=config_loader_service,
    )
    assert env_inst is not None
    assert isinstance(env_inst, Environment)
