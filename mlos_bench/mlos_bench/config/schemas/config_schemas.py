#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A simple class for describing where to find different `json config schemas
<https://json-schema.org>`_ and validating configs against them.

Used by the :py:class:`~mlos_bench.launcher.Launcher` and
:py:class:`~mlos_bench.services.config_persistence.ConfigPersistenceService` to
validate configs on load.

Notes
-----
- See `mlos_bench/config/schemas/README.md
  <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/schemas/>`_
  for additional documentation in the source tree.

- See `mlos_bench/config/README.md
  <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/>`_
  for additional config examples in the source tree.
"""

import json  # schema files are pure json - no comments
import logging
from collections.abc import Iterator, Mapping
from enum import Enum
from os import environ, path, walk

import jsonschema
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from mlos_bench.util import path_join

_LOG = logging.getLogger(__name__)

# The path to find all config schemas.
CONFIG_SCHEMA_DIR = path_join(path.dirname(__file__), abs_path=True)
"""The local directory where all config schemas shipped as a part of the
:py:mod:`mlos_bench` module are stored.
"""

# Allow skipping schema validation for tight dev cycle changes.
# It is used in `ConfigSchema.validate()` method below.
# NOTE: this may cause pytest to fail if it's expecting exceptions
# to be raised for invalid configs.
VALIDATION_ENV_FLAG = "MLOS_BENCH_SKIP_SCHEMA_VALIDATION"
"""
The special environment flag to set to skip schema validation when "true".

Useful for local development when you're making a lot of changes to the config or adding
new classes that aren't in the main repo yet.
"""

_SKIP_VALIDATION = environ.get(VALIDATION_ENV_FLAG, "false").lower() in {
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
    _SCHEMA_STORE: dict[str, dict] = {}
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
                with open(file_path, encoding="utf-8") as schema_file:
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
"""Static :py:class:`.SchemaStore` instance used for storing and retrieving schemas for
config validation.
"""


class ConfigSchema(Enum):
    """An enum to help describe schema types and help validate configs against them."""

    CLI = path_join(CONFIG_SCHEMA_DIR, "cli/cli-schema.json")
    """
    Json config `schema
    <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/schemas/cli/cli-schema.json>`__
    for :py:mod:`mlos_bench <mlos_bench.run>` CLI configuration.

    See Also
    --------
    mlos_bench.config : documentation on the configuration system.
    mlos_bench.launcher.Launcher : class is responsible for processing the CLI args.
    """

    GLOBALS = path_join(CONFIG_SCHEMA_DIR, "cli/globals-schema.json")
    """
    Json config `schema
    <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/schemas/cli/globals-schema.json>`__
    for :py:mod:`global variables <mlos_bench.config>`.
    """

    ENVIRONMENT = path_join(CONFIG_SCHEMA_DIR, "environments/environment-schema.json")
    """
    Json config `schema
    <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/schemas/environments/environment-schema.json>`__
    for :py:mod:`~mlos_bench.environments`.
    """

    OPTIMIZER = path_join(CONFIG_SCHEMA_DIR, "optimizers/optimizer-schema.json")
    """
    Json config `schema
    <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/schemas/optimizers/optimizer-schema.json>`__
    for :py:mod:`~mlos_bench.optimizers`.
    """

    SCHEDULER = path_join(CONFIG_SCHEMA_DIR, "schedulers/scheduler-schema.json")
    """
    Json config `schema
    <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/schemas/schedulers/scheduler-schema.json>`__
    for :py:mod:`~mlos_bench.schedulers`.
    """

    SERVICE = path_join(CONFIG_SCHEMA_DIR, "services/service-schema.json")
    """
    Json config `schema
    <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/schemas/services/service-schema.json>`__
    for :py:mod:`~mlos_bench.services`.
    """

    STORAGE = path_join(CONFIG_SCHEMA_DIR, "storage/storage-schema.json")
    """
    Json config `schema
    <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/schemas/storage/storage-schema.json>`__
    for :py:mod:`~mlos_bench.storage` instances.
    """

    TUNABLE_PARAMS = path_join(CONFIG_SCHEMA_DIR, "tunables/tunable-params-schema.json")
    """
    Json config `schema
    <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/schemas/tunables/tunable-params-schema.json>`__
    for :py:mod:`~mlos_bench.tunables` instances.
    """

    TUNABLE_VALUES = path_join(CONFIG_SCHEMA_DIR, "tunables/tunable-values-schema.json")
    """
    Json config `schema
    <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/schemas/tunables/tunable-values-schema.json>`__
    for values of :py:mod:`~mlos_bench.tunables.tunable_groups.TunableGroups` instances.

    These can be used to specify the values of the tunables for a given experiment
    using the :py:class:`~mlos_bench.optimizers.one_shot_optimizer.OneShotOptimizer`
    for instance.
    """

    UNIFIED = path_join(CONFIG_SCHEMA_DIR, "mlos-bench-config-schema.json")
    """
    Combined global json `schema
    <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/schemas/mlos-bench-config-schema.json>`__
    use to validate any ``mlos_bench`` config file (e.g., ``*.mlos.jsonc`` files).

    See Also
    --------
    <https://www.schemastore.org/json/>
    """

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
            On validation failure.
        jsonschema.exceptions.SchemaError
            On schema loading error.
        """
        if _SKIP_VALIDATION:
            _LOG.warning("%s is set - skip schema validation", VALIDATION_ENV_FLAG)
        else:
            jsonschema.Draft202012Validator(
                schema=self.schema,
                registry=SCHEMA_STORE.registry,
            ).validate(config)
