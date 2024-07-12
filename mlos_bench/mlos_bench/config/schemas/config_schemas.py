#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A simple class for describing where to find different config schemas and validating
configs against them.
"""

import json  # schema files are pure json - no comments
import logging
from enum import Enum
from os import environ, path, walk
from typing import Dict, Iterator, Mapping

import jsonschema
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from mlos_bench.util import path_join

_LOG = logging.getLogger(__name__)

# The path to find all config schemas.
CONFIG_SCHEMA_DIR = path_join(path.dirname(__file__), abs_path=True)

# Allow skipping schema validation for tight dev cycle changes.
# It is used in `ConfigSchema.validate()` method below.
# NOTE: this may cause pytest to fail if it's expecting exceptions
# to be raised for invalid configs.
_VALIDATION_ENV_FLAG = "MLOS_BENCH_SKIP_SCHEMA_VALIDATION"
_SKIP_VALIDATION = environ.get(_VALIDATION_ENV_FLAG, "false").lower() in {
    "true",
    "y",
    "yes",
    "on",
    "1",
}


# Note: we separate out the SchemaStore from a class method on ConfigSchema
# because of issues with mypy/pylint and non-Enum-member class members.
class SchemaStore(Mapping):
    """A simple class for storing schemas and subschemas for the validator to
    reference.
    """

    # A class member mapping of schema id to schema object.
    _SCHEMA_STORE: Dict[str, dict] = {}
    _REGISTRY: Registry = Registry()

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
        """Loads all schemas and subschemas into the schema store for the validator to
        reference.
        """
        if cls._SCHEMA_STORE:
            return
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
                    assert "$id" in schema
                    assert schema["$id"] not in cls._SCHEMA_STORE
                    cls._SCHEMA_STORE[schema["$id"]] = schema

    @classmethod
    def _load_registry(cls) -> None:
        """Also store them in a Registry object for referencing by recent versions of
        jsonschema.
        """
        if not cls._SCHEMA_STORE:
            cls._load_schemas()
        cls._REGISTRY = Registry().with_resources(
            [
                (url, Resource.from_contents(schema, default_specification=DRAFT202012))
                for url, schema in cls._SCHEMA_STORE.items()
            ]
        )

    @property
    def registry(self) -> Registry:
        """Returns a Registry object with all the schemas loaded."""
        if not self._REGISTRY:
            self._load_registry()
        return self._REGISTRY


SCHEMA_STORE = SchemaStore()


class ConfigSchema(Enum):
    """An enum to help describe schema types and help validate configs against them."""

    CLI = path_join(CONFIG_SCHEMA_DIR, "cli/cli-schema.json")
    GLOBALS = path_join(CONFIG_SCHEMA_DIR, "cli/globals-schema.json")
    ENVIRONMENT = path_join(CONFIG_SCHEMA_DIR, "environments/environment-schema.json")
    OPTIMIZER = path_join(CONFIG_SCHEMA_DIR, "optimizers/optimizer-schema.json")
    SCHEDULER = path_join(CONFIG_SCHEMA_DIR, "schedulers/scheduler-schema.json")
    SERVICE = path_join(CONFIG_SCHEMA_DIR, "services/service-schema.json")
    STORAGE = path_join(CONFIG_SCHEMA_DIR, "storage/storage-schema.json")
    TUNABLE_PARAMS = path_join(CONFIG_SCHEMA_DIR, "tunables/tunable-params-schema.json")
    TUNABLE_VALUES = path_join(CONFIG_SCHEMA_DIR, "tunables/tunable-values-schema.json")

    UNIFIED = path_join(CONFIG_SCHEMA_DIR, "mlos-bench-config-schema.json")

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
            The config to validate.

        Raises
        ------
        jsonschema.exceptions.ValidationError
        jsonschema.exceptions.SchemaError
        """
        if _SKIP_VALIDATION:
            _LOG.warning("%s is set - skip schema validation", _VALIDATION_ENV_FLAG)
        else:
            jsonschema.Draft202012Validator(
                schema=self.schema,
                registry=SCHEMA_STORE.registry,
            ).validate(config)
