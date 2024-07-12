#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for loading globals config examples."""
import logging
from typing import List

import pytest

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.tests.config import BUILTIN_TEST_CONFIG_PATH, locate_config_examples

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


# Get the set of configs to test.
CONFIG_TYPE = "globals"


def filter_configs(configs_to_filter: List[str]) -> List[str]:
    """If necessary, filter out json files that aren't for the module we're testing."""
    return configs_to_filter


configs = [
    # *locate_config_examples(
    #    ConfigPersistenceService.BUILTIN_CONFIG_PATH,
    #    CONFIG_TYPE,
    #    filter_configs,
    # ),
    *locate_config_examples(
        ConfigPersistenceService.BUILTIN_CONFIG_PATH,
        "experiments",
        filter_configs,
    ),
    *locate_config_examples(
        BUILTIN_TEST_CONFIG_PATH,
        CONFIG_TYPE,
        filter_configs,
    ),
    *locate_config_examples(
        BUILTIN_TEST_CONFIG_PATH,
        "experiments",
        filter_configs,
    ),
]
assert configs


@pytest.mark.parametrize("config_path", configs)
def test_load_globals_config_examples(
    config_loader_service: ConfigPersistenceService,
    config_path: str,
) -> None:
    """Tests loading a config example."""
    config = config_loader_service.load_config(config_path, ConfigSchema.GLOBALS)
    assert isinstance(config, dict)
