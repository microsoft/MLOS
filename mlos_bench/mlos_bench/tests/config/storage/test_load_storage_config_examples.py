#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for loading storage config examples.
"""

from typing import List

import importlib
import logging
import os

import pytest

from mlos_bench.tests.config import locate_config_examples
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable_groups import TunableGroups


_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


# Get the set of configs to test.
CONFIG_TYPE = "storage"


def filter_configs(configs_to_filter: List[str]) -> List[str]:
    """If necessary, filter out json files that aren't for the module we're testing."""
    return configs_to_filter


configs = filter_configs(locate_config_examples(os.path.join(ConfigPersistenceService.BUILTIN_CONFIG_PATH, CONFIG_TYPE)))
assert configs


@pytest.mark.parametrize("config_path", configs)
def test_load_storage_config_examples(config_path: str) -> None:
    """Tests loading a config example."""
    config_loader_service = ConfigPersistenceService()
    _LOG.info("Loading config %s", config_path)
    config = config_loader_service.load_config(config_path)
    assert isinstance(config, dict)
    #config["config"]["lazy_connect"] = True
    config["config"]["lazy_schema_create"] = True
    cls_fqn: str = config["class"]
    _LOG.info("Loading %s", cls_fqn)
    module = importlib.import_module(str.join(".", (cls_fqn.split(".")[0:-1])))
    cls = getattr(module, cls_fqn.split(".")[-1])
    assert isinstance(cls, type)
    storage_inst = config_loader_service.build_generic(
        base_cls=cls,
        tunables=TunableGroups(),
        service=config_loader_service,
        config=config,
    )
    assert storage_inst is not None
    assert isinstance(storage_inst, Storage)
