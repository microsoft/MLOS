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

import jsonschema
import pytest

from mlos_core.optimizers import OptimizerType
from mlos_bench.config.schemas import ConfigSchemaType


OPTIMIZER_SCHEMA = ConfigSchemaType.OPTIMIZER.schema


def full_optimizer_config(optimizer_type: OptimizerType) -> dict:
    """
    Returns a good optimizer config with all possible options enabled.
    """
    if optimizer_type == OptimizerType.EMUKIT:
        raise NotImplementedError("TODO")
    elif optimizer_type == OptimizerType.RANDOM:
        raise NotImplementedError("TODO")
    elif optimizer_type == OptimizerType.SKOPT:
        raise NotImplementedError("TODO")
    else:
        raise NotImplementedError(f"Unhandled OptimizerType: {optimizer_type}")


# FIXME: need to parameterize the mlos_bench optimizers, and then the mlos_core optimizers
@pytest.mark.parametrize("optimizer_type", [member for member in OptimizerType])
def test_optimizer_configs_against_schema(optimizer_type: OptimizerType) -> None:
    """
    Checks that the optimizer config validates against the schema.
    """
    config = full_optimizer_config(optimizer_type)
    jsonschema.validate(config, OPTIMIZER_SCHEMA)

    optimizer_class: str = full_optimizer_config["class"]

    if optimizer_class == "mlos_bench.optimizers.MockOptimizer":
        assert optimizer_type
        del optimizer_class["config"]["use_defaults"]
    else:
        raise NotImplementedError(f"Unhandled optimizer class: {optimizer_class}")
