#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for optimizer schema validation.
"""

from copy import deepcopy
from os import path
from typing import Dict, Optional

import jsonschema
import pytest

from mlos_core.optimizers import OptimizerType
from mlos_core.spaces.adapters import SpaceAdapterType
from mlos_core.tests import get_all_concrete_subclasses

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.optimizers.base_optimizer import Optimizer

from mlos_bench.tests import try_resolve_class_name
from mlos_bench.tests.config.schemas import get_schema_test_cases, SchemaTestCaseInfo, EXTRA_CONFIG_ATTR, EXTRA_OUTER_ATTR


# General testing strategy:
# - hand code a set of good/bad configs (useful to test editor schema checking)
# - enumerate and try to check that we've covered all the cases
# - for each config, load and validate against expected schema

TEST_CASES: Dict[str, SchemaTestCaseInfo] = get_schema_test_cases(path.join(path.dirname(__file__), "test-cases"))
TEST_CASES_BY_TYPE: Dict[str, Dict[str, SchemaTestCaseInfo]] = {}
TEST_CASES_BY_SUBTYPE: Dict[str, Dict[str, SchemaTestCaseInfo]] = {}
for test_case_info in TEST_CASES.values():
    TEST_CASES_BY_TYPE.setdefault(test_case_info["test_case_type"], {})
    TEST_CASES_BY_TYPE[test_case_info["test_case_type"]][test_case_info["test_case"]] = test_case_info
    TEST_CASES_BY_SUBTYPE.setdefault(test_case_info["test_case_subtype"], {})
    TEST_CASES_BY_SUBTYPE[test_case_info["test_case_subtype"]][test_case_info["test_case"]] = test_case_info

assert len(TEST_CASES_BY_TYPE["good"].keys()) > 0
assert len(TEST_CASES_BY_TYPE["bad"].keys()) > 0
assert len(TEST_CASES_BY_SUBTYPE.keys()) > 2


# Dynamically enumerate some of the cases we want to make sure we cover.

expected_mlos_bench_optimizer_class_names = [subclass.__module__ + "." + subclass.__name__
                                             for subclass in get_all_concrete_subclasses(Optimizer)]  # type: ignore[type-abstract]
assert expected_mlos_bench_optimizer_class_names

# Also make sure that we check for configs where the optimizer_type or space_adapter_type are left unspecified (None).

expected_mlos_core_optimizer_types = list(OptimizerType) + [None]
assert expected_mlos_core_optimizer_types

expected_mlos_core_space_adapter_types = list(SpaceAdapterType) + [None]
assert expected_mlos_core_space_adapter_types


# Do the full cross product of all the test cases and all the optimizer types.
@pytest.mark.parametrize("test_case_subtype", list(TEST_CASES_BY_SUBTYPE.keys()))
@pytest.mark.parametrize("mlos_bench_optimizer_type", expected_mlos_bench_optimizer_class_names)
def test_case_coverage_mlos_bench_optimizer_type(test_case_subtype: str, mlos_bench_optimizer_type: str) -> None:
    """
    Checks to see if there is a given type of test case for the given mlos_bench optimizer type.
    """
    for test_case in TEST_CASES_BY_SUBTYPE[test_case_subtype].values():
        if try_resolve_class_name(test_case["config"].get("class")) == mlos_bench_optimizer_type:
            return
    raise NotImplementedError(
        f"Missing test case for subtype {test_case_subtype} for Optimizer class {mlos_bench_optimizer_type}")

# Being a little lazy for the moment and relaxing the requirement that we have
# a subtype test case for each optimizer and space adapter combo.


@pytest.mark.parametrize("test_case_type", list(TEST_CASES_BY_TYPE.keys()))
# @pytest.mark.parametrize("test_case_subtype", list(TEST_CASES_BY_SUBTYPE.keys()))
@pytest.mark.parametrize("mlos_core_optimizer_type", expected_mlos_core_optimizer_types)
def test_case_coverage_mlos_core_optimizer_type(test_case_type: str,
                                                mlos_core_optimizer_type: Optional[OptimizerType]) -> None:
    """
    Checks to see if there is a given type of test case for the given mlos_core optimizer type.
    """
    optimizer_name = None if mlos_core_optimizer_type is None else mlos_core_optimizer_type.name
    for test_case in TEST_CASES_BY_TYPE[test_case_type].values():
        if try_resolve_class_name(test_case["config"].get("class")) \
                == "mlos_bench.optimizers.mlos_core_optimizer.MlosCoreOptimizer":
            optimizer_type = None
            if test_case["config"].get("config"):
                optimizer_type = test_case["config"]["config"].get("optimizer_type", None)
            if optimizer_type == optimizer_name:
                return
    raise NotImplementedError(
        f"Missing test case for type {test_case_type} for MlosCore Optimizer type {mlos_core_optimizer_type}")


@pytest.mark.parametrize("test_case_type", list(TEST_CASES_BY_TYPE.keys()))
# @pytest.mark.parametrize("test_case_subtype", list(TEST_CASES_BY_SUBTYPE.keys()))
@pytest.mark.parametrize("mlos_core_space_adapter_type", expected_mlos_core_space_adapter_types)
def test_case_coverage_mlos_core_space_adapter_type(test_case_type: str,
                                                    mlos_core_space_adapter_type: Optional[SpaceAdapterType]) -> None:
    """
    Checks to see if there is a given type of test case for the given mlos_core space adapter type.
    """
    space_adapter_name = None if mlos_core_space_adapter_type is None else mlos_core_space_adapter_type.name
    for test_case in TEST_CASES_BY_TYPE[test_case_type].values():
        if try_resolve_class_name(test_case["config"].get("class")) \
                == "mlos_bench.optimizers.mlos_core_optimizer.MlosCoreOptimizer":
            space_adapter_type = None
            if test_case["config"].get("config"):
                space_adapter_type = test_case["config"]["config"].get("space_adapter_type", None)
            if space_adapter_type == space_adapter_name:
                return
    raise NotImplementedError(
        f"Missing test case for type {test_case_type} for SpaceAdapter type {mlos_core_space_adapter_type}")


# Now we actually perform all of those validation tests.

@pytest.mark.parametrize("test_case_name", list(TEST_CASES.keys()))
def test_optimizer_configs_against_schema(test_case_name: str) -> None:
    """
    Checks that the optimizer config validates against the schema.
    """
    test_case = TEST_CASES[test_case_name]
    if test_case["test_case_type"] == "good":
        ConfigSchema.OPTIMIZER.validate(test_case["config"])
    elif test_case["test_case_type"] == "bad":
        with pytest.raises(jsonschema.ValidationError):
            ConfigSchema.OPTIMIZER.validate(test_case["config"])
    else:
        raise NotImplementedError(f"Unknown test case type: {test_case['test_case_type']}")


def test_optimizer_configs_with_extra_param() -> None:
    """
    Checks that the optimizer config fails to validate if extra params are present in certain places.
    """
    test_case = next(iter(TEST_CASES_BY_TYPE["good"].values()))
    config = deepcopy(test_case["config"])
    ConfigSchema.OPTIMIZER.validate(config)
    config[EXTRA_OUTER_ATTR] = "should not be here"
    with pytest.raises(jsonschema.ValidationError):
        ConfigSchema.OPTIMIZER.validate(config)
    del config[EXTRA_OUTER_ATTR]
    if not config.get("config"):
        config["config"] = {}
    config["config"][EXTRA_CONFIG_ATTR] = "should not be here"
    with pytest.raises(jsonschema.ValidationError):
        ConfigSchema.OPTIMIZER.validate(config)
