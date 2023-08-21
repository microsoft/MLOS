#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests to check the main CLI launcher.
"""
import os
from typing import List

import pytest

from mlos_bench.launcher import Launcher
from mlos_bench.util import path_join

# pylint: disable=redefined-outer-name


@pytest.fixture
def root_path() -> str:
    """
    Root path of mlos_bench project.
    """
    return path_join(os.path.dirname(__file__), "../../..", abs_path=True)


@pytest.fixture
def config_paths(root_path: str) -> List[str]:
    """
    Returns a list of config paths.

    Returns
    -------
    List[str]
    """
    return [
        path_join(root_path, 'mlos_bench/mlos_bench/config'),
        path_join(root_path, 'mlos_bench/mlos_bench/tests/config'),
    ]


@pytest.fixture
def minimal_launcher_args(config_paths: List[str]) -> List[str]:
    """
    Returns a list of minimal args necessary for the Launcher.
    """
    return [
        '--config-paths', *config_paths,    # provides two config paths as space separate args
        '--environment', 'environments/mock/mock_env.jsonc',
    ]


def test_launcher_args_parse_globals(minimal_launcher_args: List[str]) -> None:
    """
    Test argument parsing.
    """
    launcher = Launcher(description="test", argv=[
        *minimal_launcher_args,
        # Check that both --globals files are loaded when multiple args are provided.
        '--globals', 'globals/global_test_config.jsonc',
        '--globals', 'globals/global_test_extra_config.jsonc',
        # Check that --some-unknown-key values are loaded into the global config.
        '--test_global_value_2', 'from-args',
    ])
    # Check that the first --globals file is loaded and $var expansion is handled.
    assert launcher.global_config['experiment_id'] == 'MockExperiment'
    assert launcher.global_config['testVmName'] == 'MockExperiment-vm'
    assert launcher.global_config['testVnetName'] == 'MockExperiment-vnet'
    # Check that the second --globals file is loaded.
    assert launcher.global_config['test_global_value'] == 'from-file'
    # Check overriding values in a file from the command line.
    assert launcher.global_config['test_global_value_2'] == 'from-args'
