#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests to check the main CLI launcher.
"""
import sys
from typing import List

import pytest

from mlos_bench.launcher import Launcher

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
        str(files('mlos_bench.config')),
        str(files('mlos_bench.tests.config')),
    ]


@pytest.fixture
def env_conf_path() -> str:
    """
    Returns the path to a test environment config file.
    This is part of the minimal required args by the Launcher.
    """
    return 'environments/mock/mock_env.jsonc'


def test_launcher_args_parse_globals(config_paths: List[str], env_conf_path: str) -> None:
    """
    Test that using multiple --globals arguments works and that multiple space
    separated options to --config-paths works.
    """
    cli_args = '--config-paths ' + ' '.join(config_paths) + \
        f' --environment {env_conf_path}' + \
        ' --globals globals/global_test_config.jsonc' + \
        ' --globals globals/global_test_extra_config.jsonc' \
        ' --test_global_value_2 from-args'
    launcher = Launcher(description=__name__, argv=cli_args.split())
    # Check that the first --globals file is loaded and $var expansion is handled.
    assert launcher.global_config['experiment_id'] == 'MockExperiment'
    assert launcher.global_config['testVmName'] == 'MockExperiment-vm'
    # Check that secondary expansion also works.
    assert launcher.global_config['testVnetName'] == 'MockExperiment-vm-vnet'
    # Check that the second --globals file is loaded.
    assert launcher.global_config['test_global_value'] == 'from-file'
    # Check overriding values in a file from the command line.
    assert launcher.global_config['test_global_value_2'] == 'from-args'
    assert launcher.teardown


def test_launcher_args_parse_multiple_config_paths(config_paths: List[str], env_conf_path: str) -> None:
    """
    Test multiple --config-path instances.
    """
    cli_args = ' '.join([f"--config-path {config_path}" for config_path in config_paths]) + \
        f' --environment {env_conf_path}' + \
        ' --globals globals/global_test_config.jsonc' + \
        ' --experiment_id MockeryExperiment' + \
        ' --no-teardown'
    launcher = Launcher(description="test", argv=cli_args.split())
    # Check that the --globals file is loaded and $var expansion is handled
    # using the value provided on the CLI.
    assert launcher.global_config['experiment_id'] == 'MockeryExperiment'
    assert launcher.global_config['testVmName'] == 'MockeryExperiment-vm'
    # Check that secondary expansion also works.
    assert launcher.global_config['testVnetName'] == 'MockeryExperiment-vm-vnet'
    assert not launcher.teardown


# TODO: Test config file vs. args parsing.
# See Also: test_load_cli_config_examples.py
