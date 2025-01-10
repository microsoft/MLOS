#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests to check the Launcher CLI arg parsing
See Also: test_load_cli_config_examples.py
"""

import os
import sys
from getpass import getuser
from importlib.resources import files

import pytest

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.launcher import Launcher
from mlos_bench.optimizers import MlosCoreOptimizer, OneShotOptimizer
from mlos_bench.os_environ import environ
from mlos_bench.schedulers import SyncScheduler
from mlos_bench.services.types import (
    SupportsAuth,
    SupportsConfigLoading,
    SupportsFileShareOps,
    SupportsLocalExec,
    SupportsRemoteExec,
)
from mlos_bench.tests import check_class_name
from mlos_bench.util import path_join

# pylint: disable=redefined-outer-name


@pytest.fixture
def config_paths() -> list[str]:
    """
    Returns a list of config paths.

    Returns
    -------
    list[str]
    """
    return [
        path_join(os.getcwd(), abs_path=True),
        str(files("mlos_bench.config")),
        str(files("mlos_bench.tests.config")),
    ]


# This is part of the minimal required args by the Launcher.
ENV_CONF_PATH = "environments/mock/mock_env.jsonc"


def _get_launcher(desc: str, cli_args: str) -> Launcher:
    # The VSCode pytest wrapper actually starts in a different directory before
    # changing into the code directory, but doesn't update the PWD environment
    # variable so we use a separate variable.
    # See global_test_config.jsonc for more details.
    environ["CUSTOM_PATH_FROM_ENV"] = os.getcwd()
    if sys.platform == "win32":
        # Some env tweaks for platform compatibility.
        environ["USER"] = environ["USERNAME"]
    launcher = Launcher(description=desc, argv=cli_args.split())
    # Check the basic parent service
    assert isinstance(launcher.service, SupportsConfigLoading)  # built-in
    assert isinstance(launcher.service, SupportsLocalExec)  # built-in
    return launcher


def test_launcher_args_parse_defaults(config_paths: list[str]) -> None:
    """Test that we get the defaults we expect when using minimal config arg
    examples.
    """
    cli_args = (
        "--config-paths "
        + " ".join(config_paths)
        + f" --environment {ENV_CONF_PATH}"
        + " --globals globals/global_test_config.jsonc"
    )
    launcher = _get_launcher(__name__, cli_args)
    # Check that the first --globals file is loaded and $var expansion is handled.
    assert launcher.global_config["experiment_id"] == "MockExperiment"
    assert launcher.global_config["testVmName"] == "MockExperiment-vm"
    # Check that secondary expansion also works.
    assert launcher.global_config["testVnetName"] == "MockExperiment-vm-vnet"
    # Check that we can expand a $var in a config file that references an environment variable.
    assert path_join(launcher.global_config["pathVarWithEnvVarRef"], abs_path=True) == path_join(
        os.getcwd(), "foo", abs_path=True
    )
    assert launcher.global_config["varWithEnvVarRef"] == f"user:{getuser()}"
    assert launcher.teardown  # defaults
    # Check that the environment that got loaded looks to be of the right type.
    env_config = launcher.config_loader.load_config(ENV_CONF_PATH, ConfigSchema.ENVIRONMENT)
    assert env_config["class"] == "mlos_bench.environments.mock_env.MockEnv"
    assert check_class_name(launcher.environment, env_config["class"])
    # Check that the optimizer looks right.
    assert isinstance(launcher.optimizer, OneShotOptimizer)
    # Check that the optimizer got initialized with defaults.
    assert launcher.optimizer.tunable_params.is_defaults()
    assert launcher.optimizer.max_suggestions == 1  # value for OneShotOptimizer
    # Check that we pick up the right scheduler config:
    assert isinstance(launcher.scheduler, SyncScheduler)
    assert launcher.scheduler.trial_config_repeat_count == 1  # default
    assert launcher.scheduler.max_trials == -1  # default


def test_launcher_args_parse_1(config_paths: list[str]) -> None:
    """
    Test that using multiple --globals arguments works and that multiple space separated
    options to --config-paths works.

    Check $var expansion and Environment loading.
    """
    # Here we have multiple paths following --config-paths and --service.
    cli_args = (
        "--config-paths "
        + " ".join(config_paths)
        + " --service services/remote/mock/mock_auth_service.jsonc"
        " services/remote/mock/mock_remote_exec_service.jsonc"
        " --scheduler schedulers/sync_scheduler.jsonc"
        f" --environment {ENV_CONF_PATH}"
        " --globals globals/global_test_config.jsonc"
        " --globals globals/global_test_extra_config.jsonc"
        " --test_global_value_2 from-args"
    )
    launcher = _get_launcher(__name__, cli_args)
    # Check some additional features of the the parent service
    assert isinstance(launcher.service, SupportsAuth)  # from --service
    assert isinstance(launcher.service, SupportsRemoteExec)  # from --service
    # Check that the first --globals file is loaded and $var expansion is handled.
    assert launcher.global_config["experiment_id"] == "MockExperiment"
    assert launcher.global_config["testVmName"] == "MockExperiment-vm"
    # Check that secondary expansion also works.
    assert launcher.global_config["testVnetName"] == "MockExperiment-vm-vnet"
    # Check that the second --globals file is loaded.
    assert launcher.global_config["test_global_value"] == "from-file"
    # Check overriding values in a file from the command line.
    assert launcher.global_config["test_global_value_2"] == "from-args"
    # Check that we can expand a $var in a config file that references an environment variable.
    assert path_join(launcher.global_config["pathVarWithEnvVarRef"], abs_path=True) == path_join(
        os.getcwd(), "foo", abs_path=True
    )
    assert launcher.global_config["varWithEnvVarRef"] == f"user:{getuser()}"
    assert launcher.teardown
    # Check that the environment that got loaded looks to be of the right type.
    env_config = launcher.config_loader.load_config(ENV_CONF_PATH, ConfigSchema.ENVIRONMENT)
    assert env_config["class"] == "mlos_bench.environments.mock_env.MockEnv"
    # Check that the optimizer looks right.
    assert isinstance(launcher.optimizer, OneShotOptimizer)
    # Check that the optimizer got initialized with defaults.
    assert launcher.optimizer.tunable_params.is_defaults()
    assert launcher.optimizer.max_suggestions == 1  # value for OneShotOptimizer
    # Check that we pick up the right scheduler config:
    assert isinstance(launcher.scheduler, SyncScheduler)
    assert (
        launcher.scheduler.trial_config_repeat_count == 3
    )  # from the custom sync_scheduler.jsonc config
    assert launcher.scheduler.max_trials == -1


def test_launcher_args_parse_2(config_paths: list[str]) -> None:
    """Test multiple --config-path instances, --config file vs --arg, --var=val
    overrides, $var templates, option args, --random-init, etc.
    """
    config_file = "cli/test-cli-config.jsonc"
    globals_file = "globals/global_test_config.jsonc"
    # Here we have multiple --config-path and --service args, each with their own path.
    cli_args = (
        " ".join([f"--config-path {config_path}" for config_path in config_paths])
        + f" --config {config_file}"
        " --service services/remote/mock/mock_auth_service.jsonc"
        " --service services/remote/mock/mock_remote_exec_service.jsonc"
        f" --globals {globals_file}"
        " --experiment_id MockeryExperiment"
        " --no-teardown"
        " --random-init"
        " --random-seed 1234"
        " --trial-config-repeat-count 5"
        " --max_trials 200"
    )
    launcher = _get_launcher(__name__, cli_args)
    # Check some additional features of the the parent service
    assert isinstance(launcher.service, SupportsAuth)  # from --service
    assert isinstance(launcher.service, SupportsFileShareOps)  # from --config
    assert isinstance(launcher.service, SupportsRemoteExec)  # from --service
    # Check that the --globals file is loaded and $var expansion is handled
    # using the value provided on the CLI.
    assert launcher.global_config["experiment_id"] == "MockeryExperiment"
    assert launcher.global_config["testVmName"] == "MockeryExperiment-vm"
    # Check that secondary expansion also works.
    assert launcher.global_config["testVnetName"] == "MockeryExperiment-vm-vnet"
    # Check that we can expand a $var in a config file that references an environment variable.
    assert path_join(launcher.global_config["pathVarWithEnvVarRef"], abs_path=True) == path_join(
        os.getcwd(), "foo", abs_path=True
    )
    assert launcher.global_config["varWithEnvVarRef"] == f"user:{getuser()}"
    assert not launcher.teardown

    config = launcher.config_loader.load_config(config_file, ConfigSchema.CLI)
    assert launcher.config_loader.config_paths == [
        path_join(path, abs_path=True) for path in config_paths + config["config_path"]
    ]

    # Check that the environment that got loaded looks to be of the right type.
    env_config_file = config["environment"]
    env_config = launcher.config_loader.load_config(env_config_file, ConfigSchema.ENVIRONMENT)
    assert check_class_name(launcher.environment, env_config["class"])

    # Check that the optimizer looks right.
    assert isinstance(launcher.optimizer, MlosCoreOptimizer)
    opt_config_file = config["optimizer"]
    opt_config = launcher.config_loader.load_config(opt_config_file, ConfigSchema.OPTIMIZER)
    globals_file_config = launcher.config_loader.load_config(globals_file, ConfigSchema.GLOBALS)
    # The actual global_config gets overwritten as a part of processing, so to test
    # this we read the original value out of the source files.
    orig_max_iters = globals_file_config.get(
        "max_suggestions", opt_config.get("config", {}).get("max_suggestions", 100)
    )
    assert (
        launcher.optimizer.max_suggestions
        == orig_max_iters
        == launcher.global_config["max_suggestions"]
    )

    # Check that the optimizer got initialized with random values instead of the defaults.
    # Note: the environment doesn't get updated until suggest() is called to
    # return these values in run.py.
    assert not launcher.optimizer.tunable_params.is_defaults()

    # TODO: Add a check that this flows through and replaces other seed config
    # values through the stack.
    # See Also: #495

    # Check that CLI parameter overrides JSON config:
    assert isinstance(launcher.scheduler, SyncScheduler)
    assert launcher.scheduler.trial_config_repeat_count == 5  # from cli args
    assert launcher.scheduler.max_trials == 200

    # Check that the value from the file is overridden by the CLI arg.
    assert config["random_seed"] == 42
    # TODO: This isn't actually respected yet because the `--random-init` only
    # applies to a temporary Optimizer used to populate the initial values via
    # random sampling.
    # assert launcher.optimizer.seed == 1234


def test_launcher_args_parse_3(config_paths: list[str]) -> None:
    """Check that cli file values take precedence over other values."""
    config_file = "cli/test-cli-config.jsonc"
    globals_file = "globals/global_test_config.jsonc"
    # Here we don't override values in test-cli-config with cli args but ensure that
    # those take precedence over other config files.
    cli_args = (
        " ".join([f"--config-path {config_path}" for config_path in config_paths])
        + f" --config {config_file}"
        f" --globals {globals_file}"
        " --max-suggestions 10"  # check for - to _ conversion too
    )
    launcher = _get_launcher(__name__, cli_args)

    assert launcher.optimizer.max_suggestions == 10  # from CLI args

    # Check that CLI file parameter overrides JSON config:
    assert isinstance(launcher.scheduler, SyncScheduler)
    # from test-cli-config.jsonc (should override scheduler config file)
    assert launcher.scheduler.trial_config_repeat_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-n0"])
