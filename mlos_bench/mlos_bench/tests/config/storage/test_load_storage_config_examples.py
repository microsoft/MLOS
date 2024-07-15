#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for loading storage config examples."""
import logging
from typing import List

import pytest

from mlos_bench.config.schemas.config_schemas import ConfigSchema
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tests.config import locate_config_examples
from mlos_bench.util import get_class_from_name

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


# Get the set of configs to test.
CONFIG_TYPE = "storage"


def filter_configs(configs_to_filter: List[str]) -> List[str]:
    """If necessary, filter out json files that aren't for the module we're testing."""
    return configs_to_filter


configs = locate_config_examples(
    ConfigPersistenceService.BUILTIN_CONFIG_PATH,
    CONFIG_TYPE,
    filter_configs,
)
assert configs


@pytest.mark.parametrize("config_path", configs)
def test_load_storage_config_examples(
    config_loader_service: ConfigPersistenceService,
    config_path: str,
) -> None:
    """Tests loading a config example."""
    config = config_loader_service.load_config(config_path, ConfigSchema.STORAGE)
    assert isinstance(config, dict)
    # Skip schema loading that would require a database connection for this test.
    config["config"]["lazy_schema_create"] = True
    cls = get_class_from_name(config["class"])
    assert issubclass(cls, Storage)
    # Make an instance of the class based on the config.
    storage_inst = config_loader_service.build_storage(
        config=config,
        service=config_loader_service,
    )
    assert storage_inst is not None
    assert isinstance(storage_inst, cls)
