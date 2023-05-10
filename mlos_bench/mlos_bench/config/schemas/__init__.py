#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A module for managing config schemas and their validation.
"""

from mlos_bench.config.schemas.config_schemas import ConfigSchema, CONFIG_SCHEMA_DIR


__all__ = [
    'ConfigSchema',
    'CONFIG_SCHEMA_DIR',
]
