#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for loading storage config examples."""

import logging
import sys
from typing import List

import pytest

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.environments import Environment
from mlos_bench.launcher import Launcher
from mlos_bench.optimizers import Optimizer
from mlos_bench.schedulers import Scheduler
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.storage import Storage
from mlos_bench.tests import check_class_name
from mlos_bench.tests.config import BUILTIN_TEST_CONFIG_PATH, locate_config_examples
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


configs = [
    *locate_config_examples(
        ConfigPersistenceService.BUILTIN_CONFIG_PATH,
        CONFIG_TYPE,
        filter_configs,
    ),
    *locate_config_examples(
        BUILTIN_TEST_CONFIG_PATH,
        CONFIG_TYPE,
        filter_configs,
    ),
]
assert configs


@pytest.mark.skip(reason="Use full Launcher test (below) instead now.")
@pytest.mark.parametrize("config_path", configs)
def test_load_cli_config_examples(
    config_loader_service: ConfigPersistenceService,
    config_path: str,
) -> None:  # pragma: no cover
    """Tests loading a config example."""
    # pylint: disable=too-complex
    config = config_loader_service.load_config(config_path, ConfigSchema.CLI)
    assert isinstance(config, dict)

    if config_paths := config.get("config_path"):
        assert isinstance(config_paths, list)
        config_paths.reverse()
        for path in config_paths:
            config_loader_service._config_path.insert(0, path)  # pylint: disable=protected-access

    # Foreach arg that references another file, see if we can at least load that too.
    args_to_skip = {
        "config_path",  # handled above
        "log_file",
        "log_level",
        "experiment_id",
        "trial_id",
        "teardown",
    }
    for arg in config:
        if arg in args_to_skip:
            continue

        if arg == "globals":
            for path in config[arg]:
                sub_config = config_loader_service.load_config(path, ConfigSchema.GLOBALS)
                assert isinstance(sub_config, dict)
        elif arg == "environment":
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


@pytest.mark.parametrize("config_path", configs)
def test_load_cli_config_examples_via_launcher(
    config_loader_service: ConfigPersistenceService,
    config_path: str,
) -> None:
    """Tests loading a config example via the Launcher."""
    config = config_loader_service.load_config(config_path, ConfigSchema.CLI)
    assert isinstance(config, dict)

    # Try to load the CLI config by instantiating a launcher.
    # To do this we need to make sure to give it a few extra paths and globals
    # to look for for our examples.
    cli_args = (
        f"--config {config_path}"
        f" --config-path {files('mlos_bench.config')} "
        f" --config-path {files('mlos_bench.tests.config')}"
        f" --config-path {path_join(str(files('mlos_bench.tests.config')), 'globals')}"
        f" --globals {files('mlos_bench.tests.config')}/experiments/experiment_test_config.jsonc"
    )
    launcher = Launcher(description=__name__, long_text=config_path, argv=cli_args.split())
    assert launcher

    # Check that some parts of that config are loaded.

    assert ConfigPersistenceService.BUILTIN_CONFIG_PATH in launcher.config_loader.config_paths
    if config_paths := config.get("config_path"):
        assert isinstance(config_paths, list)
        for path in config_paths:
            # Note: Checks that the order is maintained are handled in launcher_parse_args.py
            assert any(
                config_path.endswith(path) for config_path in launcher.config_loader.config_paths
            ), f"Expected {path} to be in {launcher.config_loader.config_paths}"

    if "experiment_id" in config:
        assert launcher.global_config["experiment_id"] == config["experiment_id"]
    if "trial_id" in config:
        assert launcher.global_config["trial_id"] == config["trial_id"]

    expected_log_level = logging.getLevelName(config.get("log_level", "INFO"))
    if isinstance(expected_log_level, int):
        expected_log_level = logging.getLevelName(expected_log_level)
    current_log_level = logging.getLevelName(logging.root.getEffectiveLevel())
    assert current_log_level == expected_log_level

    # TODO: Check that the log_file handler is set correctly.

    expected_teardown = config.get("teardown", True)
    assert launcher.teardown == expected_teardown

    # Note: Testing of "globals" processing handled in launcher_parse_args_test.py

    # Instead of just checking that the config is loaded, check that the
    # Launcher loaded the expected types as well.

    assert isinstance(launcher.environment, Environment)
    env_config = launcher.config_loader.load_config(
        config["environment"],
        ConfigSchema.ENVIRONMENT,
    )
    assert check_class_name(launcher.environment, env_config["class"])

    assert isinstance(launcher.optimizer, Optimizer)
    if "optimizer" in config:
        opt_config = launcher.config_loader.load_config(
            config["optimizer"],
            ConfigSchema.OPTIMIZER,
        )
        assert check_class_name(launcher.optimizer, opt_config["class"])

    assert isinstance(launcher.storage, Storage)
    if "storage" in config:
        storage_config = launcher.config_loader.load_config(
            config["storage"],
            ConfigSchema.STORAGE,
        )
        assert check_class_name(launcher.storage, storage_config["class"])

    assert isinstance(launcher.scheduler, Scheduler)
    if "scheduler" in config:
        scheduler_config = launcher.config_loader.load_config(
            config["scheduler"],
            ConfigSchema.SCHEDULER,
        )
        assert check_class_name(launcher.scheduler, scheduler_config["class"])

    # TODO: Check that the launcher assigns the tunables values as expected.
