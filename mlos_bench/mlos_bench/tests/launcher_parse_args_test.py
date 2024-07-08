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
from typing import List

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

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files

# pylint: disable=redefined-outer-name


@pytest.fixture
def config_paths() -> List[str]:
    """
    Returns a list of config paths.

    Returns
    -------
    List[str]
    """
    return [
        path_join(os.getcwd(), abs_path=True),
        str(files("mlos_bench.config")),
        str(files("mlos_bench.tests.config")),
    ]


def test_launcher_args_parse_1(config_paths: List[str]) -> None:
    """
    Test that using multiple --globals arguments works and that multiple space separated
    options to --config-paths works.

    Check $var expansion and Environment loading.
    """
    # The VSCode pytest wrapper actually starts in a different directory before
    # changing into the code directory, but doesn't update the PWD environment
    # variable so we use a separate variable.
    # See global_test_config.jsonc for more details.
    environ["CUSTOM_PATH_FROM_ENV"] = os.getcwd()
    if sys.platform == "win32":
        # Some env tweaks for platform compatibility.
        environ["USER"] = environ["USERNAME"]

    # This is part of the minimal required args by the Launcher.
    env_conf_path = "environments/mock/mock_env.jsonc"
    cli_args = (
        "--config-paths "
        + " ".join(config_paths)
        + " --service services/remote/mock/mock_auth_service.jsonc"
        + " --service services/remote/mock/mock_remote_exec_service.jsonc"
        + " --scheduler schedulers/sync_scheduler.jsonc"
        + f" --environment {env_conf_path}"
        + " --globals globals/global_test_config.jsonc"
        + " --globals globals/global_test_extra_config.jsonc"
        " --test_global_value_2 from-args"
    )
    launcher = Launcher(description=__name__, argv=cli_args.split())
    # Check that the parent service
    assert isinstance(launcher.service, SupportsAuth)
    assert isinstance(launcher.service, SupportsConfigLoading)
    assert isinstance(launcher.service, SupportsLocalExec)
    assert isinstance(launcher.service, SupportsRemoteExec)
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
    env_config = launcher.config_loader.load_config(env_conf_path, ConfigSchema.ENVIRONMENT)
    assert check_class_name(launcher.environment, env_config["class"])
    # Check that the optimizer looks right.
    assert isinstance(launcher.optimizer, OneShotOptimizer)
    # Check that the optimizer got initialized with defaults.
    assert launcher.optimizer.tunable_params.is_defaults()
    assert launcher.optimizer.max_iterations == 1  # value for OneShotOptimizer
    # Check that we pick up the right scheduler config:
    assert isinstance(launcher.scheduler, SyncScheduler)
    assert launcher.scheduler._trial_config_repeat_count == 3  # pylint: disable=protected-access
    assert launcher.scheduler._max_trials == -1  # pylint: disable=protected-access


def test_launcher_args_parse_2(config_paths: List[str]) -> None:
    """Test multiple --config-path instances, --config file vs --arg, --var=val
    overrides, $var templates, option args, --random-init, etc.
    """
    # The VSCode pytest wrapper actually starts in a different directory before
    # changing into the code directory, but doesn't update the PWD environment
    # variable so we use a separate variable.
    # See global_test_config.jsonc for more details.
    environ["CUSTOM_PATH_FROM_ENV"] = os.getcwd()
    if sys.platform == "win32":
        # Some env tweaks for platform compatibility.
        environ["USER"] = environ["USERNAME"]

    config_file = "cli/test-cli-config.jsonc"
    globals_file = "globals/global_test_config.jsonc"
    cli_args = (
        " ".join([f"--config-path {config_path}" for config_path in config_paths])
        + f" --config {config_file}"
        + " --service services/remote/mock/mock_auth_service.jsonc"
        + " --service services/remote/mock/mock_remote_exec_service.jsonc"
        + f" --globals {globals_file}"
        + " --experiment_id MockeryExperiment"
        + " --no-teardown"
        + " --random-init"
        + " --random-seed 1234"
        + " --trial-config-repeat-count 5"
        + " --max_trials 200"
    )
    launcher = Launcher(description=__name__, argv=cli_args.split())
    # Check that the parent service
    assert isinstance(launcher.service, SupportsAuth)
    assert isinstance(launcher.service, SupportsConfigLoading)
    assert isinstance(launcher.service, SupportsFileShareOps)
    assert isinstance(launcher.service, SupportsLocalExec)
    assert isinstance(launcher.service, SupportsRemoteExec)
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
        launcher.optimizer.max_iterations
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
    assert launcher.scheduler._trial_config_repeat_count == 5  # pylint: disable=protected-access
    assert launcher.scheduler._max_trials == 200  # pylint: disable=protected-access

    # Check that the value from the file is overridden by the CLI arg.
    assert config["random_seed"] == 42
    # TODO: This isn't actually respected yet because the `--random-init` only
    # applies to a temporary Optimizer used to populate the initial values via
    # random sampling.
    # assert launcher.optimizer.seed == 1234


if __name__ == "__main__":
    pytest.main([__file__, "-n1"])
