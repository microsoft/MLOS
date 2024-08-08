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
    parent: Service = config_loader_service
    config = config_loader_service.load_config(config_path, ConfigSchema.SERVICE)

    # Add other services that require a SupportsAuth parent service as necessary.
    # AzureFileShareService requires an AzureAuth service to be loaded as well.
    # mock_auth_service_config = "services/remote/mock/mock_auth_service.jsonc"
    azure_auth_service_config = "services/remote/azure/service-auth.jsonc"
    requires_auth_service_parent = {
        "AzureFileShareService": azure_auth_service_config,
    }
    config_class_name = str(config.get("class", "MISSING CLASS")).rsplit(".", maxsplit=1)[-1]
    if auth_service_config_path := requires_auth_service_parent.get(config_class_name):
        auth_service_config = config_loader_service.load_config(
            auth_service_config_path,
            ConfigSchema.SERVICE,
        )
        auth_service = config_loader_service.build_service(
            config=auth_service_config,
            parent=config_loader_service,
        )
        parent = auth_service

    # Make an instance of the class based on the config.
    service_inst = config_loader_service.build_service(
        config=config,
        parent=parent,
    )
    assert service_inst is not None
    assert isinstance(service_inst, Service)
