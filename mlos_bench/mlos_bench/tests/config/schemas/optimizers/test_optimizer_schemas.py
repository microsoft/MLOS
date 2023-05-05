#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for optimizer schema validation.
"""

# TODO:
# - generate correct optimizer json for each optimizer type (manually)
# - load and validate against expected schema
# - extend to included extra params that should fail

from typing import Optional

import json     # json schema files have to be in pure json for now
import jsonschema
import pytest

from mlos_bench.services.config_persistence import ConfigPersistenceService

from mlos_core.optimizers import OptimizerType


_OPTIMIZER_SCHEMA: Optional[dict] = None


@pytest.fixture
def optimizer_schema() -> dict:
    """
    Gets the optimizer schema from the json as a dictionary.
    """
    global _OPTIMIZER_SCHEMA    # pylint: disable=global-statement
    if _OPTIMIZER_SCHEMA is None:
        schema_filepath = ConfigPersistenceService().resolve_path("schemas/optimizers/optimizer-schema.json")
        with open(schema_filepath, mode="r", encoding="utf-8") as schema_file:
            _OPTIMIZER_SCHEMA = json.load(schema_file)   # type: ignore[no-any-return]
    return _OPTIMIZER_SCHEMA


@pytest.fixture(params=[member for member in OptimizerType])
def full_optimizer_config(request: pytest.FixtureRequest) -> dict:
    """
    Returns a good optimizer config.
    """
    if request.param == OptimizerType.EMUKIT:
        raise NotImplementedError("TODO")
    elif request.param == OptimizerType.RANDOM:
        raise NotImplementedError("TODO")
    elif request.param == OptimizerType.SKOPT:
        raise NotImplementedError("TODO")
    else:
        raise NotImplementedError(f"Unhandled OptimizerType: {request.param}")


def test_good_optimizer_configs_against_schema(full_optimizer_config: dict, optimizer_schema: dict) -> None:
    """
    Checks that the optimizer config validates against the schema.
    """
    jsonschema.validate(full_optimizer_config, optimizer_schema)
