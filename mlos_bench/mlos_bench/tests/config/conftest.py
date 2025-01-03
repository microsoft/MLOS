#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Test fixtures for mlos_bench config loader tests."""

from importlib.resources import files

import pytest

from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.util import path_join


@pytest.fixture
def config_loader_service() -> ConfigPersistenceService:
    """Config loader service fixture."""
    return ConfigPersistenceService(
        config={
            "config_path": [
                str(files("mlos_bench.tests.config")),
                path_join(str(files("mlos_bench.tests.config")), "globals"),
            ]
        }
    )
