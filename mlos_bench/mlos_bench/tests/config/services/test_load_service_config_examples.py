#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for loading service config examples."""
import logging
from typing import List

import pytest

from mlos_bench.config.schemas.config_schemas import ConfigSchema
from mlos_bench.services.base_service import Service
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.tests.config import locate_config_examples

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


# Get the set of configs to test.
CONFIG_TYPE = "services"


def filter_configs(configs_to_filter: List[str]) -> List[str]:
    """If necessary, filter out json files that aren't for the module we're testing."""

    def predicate(config_path: str) -> bool:
        arm_template = config_path.find(
            "services/remote/azure/arm-templates/"
        ) >= 0 and config_path.endswith(".jsonc")
        setup_rg_scripts = config_path.find("azure/scripts/setup-rg") >= 0
        return not (arm_template or setup_rg_scripts)

    return [config_path for config_path in configs_to_filter if predicate(config_path)]


configs = locate_config_examples(
    ConfigPersistenceService.BUILTIN_CONFIG_PATH,
    CONFIG_TYPE,
    filter_configs,
)
assert configs


@pytest.mark.parametrize("config_path", configs)
def test_load_service_config_examples(
    config_loader_service: ConfigPersistenceService,
    config_path: str,
) -> None:
    """Tests loading a config example."""
    config = config_loader_service.load_config(config_path, ConfigSchema.SERVICE)
    # Make an instance of the class based on the config.
    service_inst = config_loader_service.build_service(
        config=config,
        parent=config_loader_service,
    )
    assert service_inst is not None
    assert isinstance(service_inst, Service)
