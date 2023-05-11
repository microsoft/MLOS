#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for loading optimizer config examples.
"""
import logging
from typing import List

import pytest

from mlos_bench.tests.config import locate_config_examples
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import get_class_from_name, path_join


_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


# Get the set of configs to test.
CONFIG_TYPE = "optimizers"


def filter_configs(configs_to_filter: List[str]) -> List[str]:
    """If necessary, filter out json files that aren't for the module we're testing."""
    return configs_to_filter


configs = filter_configs(locate_config_examples(path_join(ConfigPersistenceService.BUILTIN_CONFIG_PATH, CONFIG_TYPE)))
assert configs


@pytest.mark.parametrize("config_path", configs)
def test_load_optimizer_config_examples(config_loader_service: ConfigPersistenceService, config_path: str) -> None:
    """Tests loading a config example."""
    config = config_loader_service.load_config(config_path)
    assert isinstance(config, dict)
    cls = get_class_from_name(config["class"])
    assert issubclass(cls, Optimizer)
    # Make an instance of the class based on the config.
    tunable_groups = TunableGroups()
    storage_inst = config_loader_service.build_generic(
        base_cls=Optimizer,     # type: ignore[type-abstract]
        tunables=tunable_groups,
        config=config,
        service=config_loader_service,
    )
    assert storage_inst is not None
    assert isinstance(storage_inst, cls)
