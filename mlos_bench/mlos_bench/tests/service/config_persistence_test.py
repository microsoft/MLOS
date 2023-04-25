#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for configuration persistence service.
"""

from importlib.resources import files

import os
import pytest

from mlos_bench.service.config_persistence import ConfigPersistenceService

# pylint: disable=redefined-outer-name


@pytest.fixture
def config_persistence_service() -> ConfigPersistenceService:
    """
    Test fixture for ConfigPersistenceService.
    """
    return ConfigPersistenceService({
        "config_path": [
            "./non-existent-dir/test/foo/bar",                      # Non-existent config path
            str(files("mlos_bench.tests.config").joinpath("")),     # Test configs (relative to mlos_bench/tests)
            str(files("mlos_bench.config").joinpath("")),           # Stock configs
        ]
    })


def test_resolve_path(config_persistence_service: ConfigPersistenceService) -> None:
    """
    Check if we can actually find a file somewhere in `config_path`.
    """
    file_path = "tunable-values-example.json"
    path = config_persistence_service.resolve_path(file_path)
    assert path.endswith(file_path)
    assert os.path.exists(path)


def test_resolve_path_fail(config_persistence_service: ConfigPersistenceService) -> None:
    """
    Check if non-existent file resolves without using `config_path`.
    """
    file_path = "foo/non-existent-config.json"
    path = config_persistence_service.resolve_path(file_path)
    assert not os.path.exists(path)
    assert path == file_path


def test_load_config(config_persistence_service: ConfigPersistenceService) -> None:
    """
    Check if we can successfully load a config file located relative to `config_path`.
    """
    tunables_data = config_persistence_service.load_config("tunable-values-example.json")
    assert tunables_data is not None
    assert isinstance(tunables_data, dict)
    assert len(tunables_data) >= 1
