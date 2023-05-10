#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A simple class for describing where to find different config schemas and validating configs against them.
"""

from enum import Enum
from os import path, walk
from typing import Dict

import json         # schema files are pure json - no comments
import jsonschema


CONFIG_SCHEMA_DIR = path.realpath(path.dirname(__file__)).replace("\\", "/")

_SCHEMA_STORE: Dict[str, dict] = {}


def _load_schemas() -> None:
    """Loads all schemas and subschemas into the schema store for the validator to reference."""
    for root, _, files in walk(CONFIG_SCHEMA_DIR):
        for file_name in files:
            if not file_name.endswith(".json"):
                continue
            file_path = path.join(root, file_name)
            if path.getsize(file_path) == 0:
                continue
            with open(file_path, mode="r", encoding="utf-8") as schema_file:
                schema = json.load(schema_file)
                _SCHEMA_STORE[file_path] = schema
                _SCHEMA_STORE[schema["$id"]] = schema


class ConfigSchema(Enum):
    """
    An enum to help describe schema types and help validate configs against them.
    """

    CLI = path.join(CONFIG_SCHEMA_DIR, "cli/cli-schema.json")
    ENVIRONMENT = path.join(CONFIG_SCHEMA_DIR, "environments/environment-schema.json")
    OPTIMIZER = path.join(CONFIG_SCHEMA_DIR, "optimizers/optimizer-schema.json")
    SERVICE = path.join(CONFIG_SCHEMA_DIR, "services/service-schema.json")
    STORAGE = path.join(CONFIG_SCHEMA_DIR, "storage/storage-schema.json")
    TUNABLE_PARAMS = path.join(CONFIG_SCHEMA_DIR, "tunables/tunable-params-schema.json")
    TUNABLE_VALUES = path.join(CONFIG_SCHEMA_DIR, "tunables/tunable-values-schema.json")

    @property
    def schema(self) -> dict:
        """Gets the schema object for this type."""
        if not _SCHEMA_STORE.get(self.value):
            _load_schemas()
        schema = _SCHEMA_STORE[self.value]
        assert schema
        return schema

    def validate(self, config: dict) -> None:
        """
        Validates the given config against this schema.

        Parameters
        ----------
        config : dict

        Raises
        ------
        jsonschema.exceptions.ValidationError
        """
        resolver: jsonschema.RefResolver = jsonschema.RefResolver.from_schema(self.schema, store=_SCHEMA_STORE)
        jsonschema.validate(instance=config, schema=self.schema, resolver=resolver)
