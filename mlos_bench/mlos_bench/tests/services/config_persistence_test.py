#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for configuration persistence service."""

import os
import sys

import pytest

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.util import path_join

if sys.version_info < (3, 9):
    from importlib_resources import files
else:
    from importlib.resources import files


# pylint: disable=redefined-outer-name


@pytest.fixture
def config_persistence_service() -> ConfigPersistenceService:
    """Test fixture for ConfigPersistenceService."""
    return ConfigPersistenceService(
        {
            "config_path": [
                "./non-existent-dir/test/foo/bar",  # Non-existent config path
                ".",  # cwd
                str(
                    files("mlos_bench.tests.config").joinpath("")
                ),  # Test configs (relative to mlos_bench/tests)
                # Shouldn't be necessary since we automatically add this.
                # str(files("mlos_bench.config").joinpath("")),         # Stock configs
            ]
        }
    )


def test_cwd_in_explicit_search_path(config_persistence_service: ConfigPersistenceService) -> None:
    """Check that CWD is in the search path in the correct place."""
    # pylint: disable=protected-access
    assert config_persistence_service._config_path is not None
    cwd = path_join(os.getcwd(), abs_path=True)
    assert config_persistence_service._config_path.index(cwd) == 1
    with pytest.raises(ValueError):
        config_persistence_service._config_path.index(cwd, 2)


def test_cwd_in_default_search_path() -> None:
    """Checks that the CWD is prepended to the search path if not explicitly present."""
    # pylint: disable=protected-access
    config_persistence_service = ConfigPersistenceService()
    assert config_persistence_service._config_path is not None
    cwd = path_join(os.getcwd(), abs_path=True)
    assert config_persistence_service._config_path.index(cwd) == 0
    with pytest.raises(ValueError):
        config_persistence_service._config_path.index(cwd, 1)


def test_resolve_stock_path(config_persistence_service: ConfigPersistenceService) -> None:
    """Check if we can actually find a file somewhere in `config_path`."""
    # pylint: disable=protected-access
    assert config_persistence_service._config_path is not None
    assert ConfigPersistenceService.BUILTIN_CONFIG_PATH in config_persistence_service._config_path
    file_path = "storage/in-memory.jsonc"
    path = config_persistence_service.resolve_path(file_path)
    assert path.endswith(file_path)
    assert os.path.exists(path)
    assert os.path.samefile(
        ConfigPersistenceService.BUILTIN_CONFIG_PATH,
        os.path.commonpath([ConfigPersistenceService.BUILTIN_CONFIG_PATH, path]),
    )


def test_resolve_path(config_persistence_service: ConfigPersistenceService) -> None:
    """Check if we can actually find a file somewhere in `config_path`."""
    file_path = "tunable-values/tunable-values-example.jsonc"
    path = config_persistence_service.resolve_path(file_path)
    assert path.endswith(file_path)
    assert os.path.exists(path)


def test_resolve_path_fail(config_persistence_service: ConfigPersistenceService) -> None:
    """Check if non-existent file resolves without using `config_path`."""
    file_path = "foo/non-existent-config.json"
    path = config_persistence_service.resolve_path(file_path)
    assert not os.path.exists(path)
    assert path == file_path


def test_load_config(config_persistence_service: ConfigPersistenceService) -> None:
    """Check if we can successfully load a config file located relative to
    `config_path`.
    """
    tunables_data = config_persistence_service.load_config(
        "tunable-values/tunable-values-example.jsonc",
        ConfigSchema.TUNABLE_VALUES,
    )
    assert tunables_data is not None
    assert isinstance(tunables_data, dict)
    assert len(tunables_data) >= 1
