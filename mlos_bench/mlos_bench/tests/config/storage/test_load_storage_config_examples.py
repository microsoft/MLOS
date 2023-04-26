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

from mlos_bench.tests.config import locate_config_examples, load_config_example
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
    # Skip schema loading that would require a database connection for this test.
    storage_inst = load_config_example(config_path, config_overrides={
        "config": {
            "lazy_schema_create": True,
        }
    })

    assert storage_inst is not None
    assert isinstance(storage_inst, Storage)
