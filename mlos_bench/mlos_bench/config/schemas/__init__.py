#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A module for managing config schemas and their validation.

See Also
--------
mlos_bench.config.schemas.config_schemas : The module handling the actual schema
    definitions and validation.
"""

from mlos_bench.config.schemas.config_schemas import CONFIG_SCHEMA_DIR, ConfigSchema

__all__ = [
    "ConfigSchema",
    "CONFIG_SCHEMA_DIR",
]
