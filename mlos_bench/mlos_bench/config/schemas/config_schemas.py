#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A simple class for describing where to find different config schemas and validating configs against them.
"""

from enum import Enum
from os import path, walk
from typing import Dict, Iterator, Mapping

import json         # schema files are pure json - no comments
import jsonschema

from mlos_bench.util import path_join


# The path to find all config schemas.
CONFIG_SCHEMA_DIR = path_join(path.dirname(__file__), abs_path=True)


# Note: we separate out the SchemaStore from a class method on ConfigSchema
# because of issues with mypy/pylint and non-Enum-member class members.
class SchemaStore(Mapping):
    """
    A simple class for storing schemas and subschemas for the validator to reference.
    """

    # A class member mapping of schema id to schema object.
    _SCHEMA_STORE: Dict[str, dict] = {}

    def __len__(self) -> int:
        return self._SCHEMA_STORE.__len__()

    def __iter__(self) -> Iterator:
        return self._SCHEMA_STORE.__iter__()

    def __getitem__(self, key: str) -> dict:
        """Gets the schema object for the given key."""
        if not self._SCHEMA_STORE:
            self._load_schemas()
        return self._SCHEMA_STORE[key]

    @classmethod
    def _load_schemas(cls) -> None:
        """Loads all schemas and subschemas into the schema store for the validator to reference."""
        for root, _, files in walk(CONFIG_SCHEMA_DIR):
            for file_name in files:
                if not file_name.endswith(".json"):
                    continue
                file_path = path_join(root, file_name)
                if path.getsize(file_path) == 0:
                    continue
                with open(file_path, mode="r", encoding="utf-8") as schema_file:
                    schema = json.load(schema_file)
                    cls._SCHEMA_STORE[file_path] = schema
                    # Let the schema be referenced by its id as well.
                    cls._SCHEMA_STORE[schema["$id"]] = schema


SCHEMA_STORE = SchemaStore()


class ConfigSchema(Enum):
    """
    An enum to help describe schema types and help validate configs against them.
    """

    CLI = path_join(CONFIG_SCHEMA_DIR, "cli/cli-schema.json")
    GLOBALS = path_join(CONFIG_SCHEMA_DIR, "cli/globals-schema.json")
    ENVIRONMENT = path_join(CONFIG_SCHEMA_DIR, "environments/environment-schema.json")
    OPTIMIZER = path_join(CONFIG_SCHEMA_DIR, "optimizers/optimizer-schema.json")
    SERVICE = path_join(CONFIG_SCHEMA_DIR, "services/service-schema.json")
    STORAGE = path_join(CONFIG_SCHEMA_DIR, "storage/storage-schema.json")
    TUNABLE_PARAMS = path_join(CONFIG_SCHEMA_DIR, "tunables/tunable-params-schema.json")
    TUNABLE_VALUES = path_join(CONFIG_SCHEMA_DIR, "tunables/tunable-values-schema.json")

    @property
    def schema(self) -> dict:
        """Gets the schema object for this type."""
        schema = SCHEMA_STORE[self.value]
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
        jsonschema.exceptions.SchemaError
        """
        resolver: jsonschema.RefResolver = jsonschema.RefResolver.from_schema(self.schema, store=SCHEMA_STORE)
        jsonschema.validate(instance=config, schema=self.schema, resolver=resolver)
