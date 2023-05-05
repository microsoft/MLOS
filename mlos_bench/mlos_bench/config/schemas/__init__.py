"""
A enum simple class for describing where to find different config schemas.
"""

from enum import Enum
from os.path import dirname, realpath
from typing import Dict

import os.path as path

import json


CONFIG_SCHEMA_DIR = realpath(dirname(__file__)).replace("\\", "/")


_SCHEMA_CACHE: Dict[str, dict] = {}


class ConfigSchemaType(Enum):
    """
    An enum to help describe schema types.
    """

    ENVIRONMENT = path.join(CONFIG_SCHEMA_DIR, "environments/environment-schema.json")
    OPTIMIZER = path.join(CONFIG_SCHEMA_DIR, "optimizers/optimizer-schema.json")
    SERVICE = path.join(CONFIG_SCHEMA_DIR, "services/service-schema.json")
    STORAGE = path.join(CONFIG_SCHEMA_DIR, "storage/storage-schema.json")
    TUNABLE_PARAMS = path.join(CONFIG_SCHEMA_DIR, "tunables/tunable-params-schema.json")
    TUNABLE_VALUES = path.join(CONFIG_SCHEMA_DIR, "tunables/tunable-values-schema.json")

    @property
    def schema(self) -> dict:
        """Gets the schema object for this type."""
        if not _SCHEMA_CACHE.get(self.name):
            with open(self.value, mode="r", encoding="utf-8") as schema_file:
                _SCHEMA_CACHE[self.name] = json.load(schema_file)
        return _SCHEMA_CACHE[self.name]
