#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for loading storage config examples.
"""

from typing import List

import logging

import pytest

from mlos_bench.tests.config import locate_config_examples

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.util import get_class_from_name, path_join


_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


# Get the set of configs to test.
CONFIG_TYPE = "cli"


def filter_configs(configs_to_filter: List[str]) -> List[str]:
    """If necessary, filter out json files that aren't for the module we're testing."""
    return configs_to_filter


configs = filter_configs(locate_config_examples(path_join(ConfigPersistenceService.BUILTIN_CONFIG_PATH, CONFIG_TYPE)))
assert configs


@pytest.mark.parametrize("config_path", configs)
def test_load_cli_config_examples(config_loader_service: ConfigPersistenceService, config_path: str) -> None:
    """Tests loading a config example."""
    config = config_loader_service.load_config(config_path, ConfigSchema.CLI)
    assert isinstance(config, dict)
    # TODO: process "config_path" first.

    # TODO: for each arg that references another file, see if we can at least load that too.
    args_to_skip = ["log_file", "log_level", "experimentId", "trialId", "teardown"]
    for arg in config:
        if arg in args_to_skip:
            continue
        if arg == "globals":
            # TODO: attempt to load the globals file, but allow it to not exist
            raise NotImplementedError("TODO")
        elif arg == "environment":
            raise NotImplementedError("TODO")
        elif arg == "optimizer":
            raise NotImplementedError("TODO")
        elif arg == "storage":
            raise NotImplementedError("TODO")
        else:
            raise NotImplementedError(f"Unhandled arg {arg} in config {config_path}")
