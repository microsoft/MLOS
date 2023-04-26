#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Test fixtures for mlos_bench config loader tests.
"""

import sys

import pytest

from mlos_bench.services.config_persistence import ConfigPersistenceService

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files


@pytest.fixture
def config_loader_service() -> ConfigPersistenceService:
    """Config loader service fixture."""
    return ConfigPersistenceService(config={
        "config_path": [
            files("mlos_bench.tests.config"),
        ]
    })
