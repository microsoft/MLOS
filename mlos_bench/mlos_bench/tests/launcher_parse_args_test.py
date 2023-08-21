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
        path_join(root_path, "mlos_bench/mlos_bench/config"),
        path_join(root_path, "mlos_bench/mlos_bench/tests/config"),
    ]


def test_launcher_args_parse_list_append(config_paths: List[str]) -> None:
    """
    Test argument parsing.
    """
    launcher = Launcher(description="test", argv=[
        "--config-paths", *config_paths,
        "--globals", "globals/global_test_config.jsonc",
        "--globals", "globals/global_test_extra_config.jsonc",
    ])
    assert 'test_global_value' in launcher.global_config
