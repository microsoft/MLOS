#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for loading storage config examples.
"""

from typing import List

import logging
import sys

import pytest

from mlos_bench.tests.config import locate_config_examples

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.launcher import Launcher
from mlos_bench.util import path_join

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files


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

    if config_paths := config.get("config_path"):
        assert isinstance(config_paths, list)
        config_paths.reverse()
        for path in config_paths:
            config_loader_service._config_path.insert(0, path)   # pylint: disable=protected-access

    # Foreach arg that references another file, see if we can at least load that too.
    args_to_skip = {
        "config_path",  # handled above
        "globals",      # we don't commit globals to the repo generally, so skip testing them
        "log_file",
        "log_level",
        "experiment_id",
        "trial_id",
        "teardown",
    }
    for arg in config:
        if arg in args_to_skip:
            continue

        if arg == "environment":
            sub_config = config_loader_service.load_config(config[arg], ConfigSchema.ENVIRONMENT)
            assert isinstance(sub_config, dict)
        elif arg == "optimizer":
            sub_config = config_loader_service.load_config(config[arg], ConfigSchema.OPTIMIZER)
            assert isinstance(sub_config, dict)
        elif arg == "storage":
            sub_config = config_loader_service.load_config(config[arg], ConfigSchema.STORAGE)
            assert isinstance(sub_config, dict)
        elif arg == "tunable_values":
            for path in config[arg]:
                sub_config = config_loader_service.load_config(path, ConfigSchema.TUNABLE_VALUES)
                assert isinstance(sub_config, dict)
        else:
            raise NotImplementedError(f"Unhandled arg {arg} in config {config_path}")

    # Try to load the CLI config by instantiating a launcher.
    cli_args = f"--config {config_path}" + \
        f" --config-path {files('mlos_bench.config')} --config-path {files('mlos_bench.tests.config')}" + \
        f" --config-path {path_join(str(files('mlos_bench.tests.config')), 'globals')}" + \
        f" --globals {files('mlos_bench.tests.config')}/experiments/experiment_test_config.jsonc"
    launcher = Launcher(description="test", argv=cli_args.split())
    assert launcher
