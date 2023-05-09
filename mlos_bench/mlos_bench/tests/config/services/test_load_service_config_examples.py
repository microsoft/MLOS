#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for loading service config examples.
"""

from typing import List

import logging
import os

import pytest

from mlos_bench.tests.config import locate_config_examples

from mlos_bench.config.schemas import ConfigSchemaType
from mlos_bench.services.base_service import Service
from mlos_bench.services.config_persistence import ConfigPersistenceService


_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


# Get the set of configs to test.
CONFIG_TYPE = "services"


def filter_configs(configs_to_filter: List[str]) -> List[str]:
    """If necessary, filter out json files that aren't for the module we're testing."""
    for config_path in configs_to_filter:
        if config_path.endswith("arm-templates/azuredeploy-ubuntu-vm.jsonc"):
            configs_to_filter.remove(config_path)
    return configs_to_filter


configs = filter_configs(locate_config_examples(os.path.join(ConfigPersistenceService.BUILTIN_CONFIG_PATH, CONFIG_TYPE)))
assert configs


@pytest.mark.parametrize("config_path", configs)
def test_load_service_config_examples(config_loader_service: ConfigPersistenceService, config_path: str) -> None:
    """Tests loading a config example."""
    config = config_loader_service.load_config(config_path, schema_type=None)   # TODO: , ConfigSchemaType.SERVICE)
    # Make an instance of the class based on the config.
    service_inst = config_loader_service.build_service(
        config=config,
        parent=config_loader_service,
    )
    assert service_inst is not None
    assert isinstance(service_inst, Service)
