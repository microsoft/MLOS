#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for optimizer schema validation."""

from os import path
from typing import Optional

import pytest

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.tests import try_resolve_class_name
from mlos_bench.tests.config.schemas import (
    check_test_case_against_schema,
    check_test_case_config_with_extra_param,
    get_schema_test_cases,
)
from mlos_core.optimizers import OptimizerType
from mlos_core.spaces.adapters import SpaceAdapterType
from mlos_core.tests import get_all_concrete_subclasses

# General testing strategy:
# - hand code a set of good/bad configs (useful to test editor schema checking)
# - enumerate and try to check that we've covered all the cases
# - for each config, load and validate against expected schema

TEST_CASES = get_schema_test_cases(path.join(path.dirname(__file__), "test-cases"))


# Dynamically enumerate some of the cases we want to make sure we cover.

expected_mlos_bench_optimizer_class_names = [
    subclass.__module__ + "." + subclass.__name__
    for subclass in get_all_concrete_subclasses(
        Optimizer,  # type: ignore[type-abstract]
        pkg_name="mlos_bench",
    )
]
assert expected_mlos_bench_optimizer_class_names

# Also make sure that we check for configs where the optimizer_type or
# space_adapter_type are left unspecified (None).

expected_mlos_core_optimizer_types = list(OptimizerType) + [None]
assert expected_mlos_core_optimizer_types

expected_mlos_core_space_adapter_types = list(SpaceAdapterType) + [None]
assert expected_mlos_core_space_adapter_types


# Do the full cross product of all the test cases and all the optimizer types.
@pytest.mark.parametrize("test_case_subtype", sorted(TEST_CASES.by_subtype))
@pytest.mark.parametrize("mlos_bench_optimizer_type", expected_mlos_bench_optimizer_class_names)
def test_case_coverage_mlos_bench_optimizer_type(
    test_case_subtype: str,
    mlos_bench_optimizer_type: str,
) -> None:
    """Checks to see if there is a given type of test case for the given mlos_bench
    optimizer type.
    """
    for test_case in TEST_CASES.by_subtype[test_case_subtype].values():
        if try_resolve_class_name(test_case.config.get("class")) == mlos_bench_optimizer_type:
            return
    raise NotImplementedError(
        f"Missing test case for subtype {test_case_subtype} "
        f"for Optimizer class {mlos_bench_optimizer_type}"
    )


# Being a little lazy for the moment and relaxing the requirement that we have
# a subtype test case for each optimizer and space adapter combo.


@pytest.mark.parametrize("test_case_type", sorted(TEST_CASES.by_type))
# @pytest.mark.parametrize("test_case_subtype", sorted(TEST_CASES.by_subtype))
@pytest.mark.parametrize("mlos_core_optimizer_type", expected_mlos_core_optimizer_types)
def test_case_coverage_mlos_core_optimizer_type(
    test_case_type: str,
    mlos_core_optimizer_type: Optional[OptimizerType],
) -> None:
    """Checks to see if there is a given type of test case for the given mlos_core
    optimizer type.
    """
    optimizer_name = None if mlos_core_optimizer_type is None else mlos_core_optimizer_type.name
    for test_case in TEST_CASES.by_type[test_case_type].values():
        if (
            try_resolve_class_name(test_case.config.get("class"))
            == "mlos_bench.optimizers.mlos_core_optimizer.MlosCoreOptimizer"
        ):
            optimizer_type = None
            if test_case.config.get("config"):
                optimizer_type = test_case.config["config"].get("optimizer_type", None)
            if optimizer_type == optimizer_name:
                return
    raise NotImplementedError(
        f"Missing test case for type {test_case_type} "
        f"for MlosCore Optimizer type {mlos_core_optimizer_type}"
    )


@pytest.mark.parametrize("test_case_type", sorted(TEST_CASES.by_type))
# @pytest.mark.parametrize("test_case_subtype", sorted(TEST_CASES.by_subtype))
@pytest.mark.parametrize("mlos_core_space_adapter_type", expected_mlos_core_space_adapter_types)
def test_case_coverage_mlos_core_space_adapter_type(
    test_case_type: str,
    mlos_core_space_adapter_type: Optional[SpaceAdapterType],
) -> None:
    """Checks to see if there is a given type of test case for the given mlos_core space
    adapter type.
    """
    space_adapter_name = (
        None if mlos_core_space_adapter_type is None else mlos_core_space_adapter_type.name
    )
    for test_case in TEST_CASES.by_type[test_case_type].values():
        if (
            try_resolve_class_name(test_case.config.get("class"))
            == "mlos_bench.optimizers.mlos_core_optimizer.MlosCoreOptimizer"
        ):
            space_adapter_type = None
            if test_case.config.get("config"):
                space_adapter_type = test_case.config["config"].get("space_adapter_type", None)
            if space_adapter_type == space_adapter_name:
                return
    raise NotImplementedError(
        f"Missing test case for type {test_case_type} "
        f"for SpaceAdapter type {mlos_core_space_adapter_type}"
    )


# Now we actually perform all of those validation tests.


@pytest.mark.parametrize("test_case_name", sorted(TEST_CASES.by_path))
def test_optimizer_configs_against_schema(test_case_name: str) -> None:
    """Checks that the optimizer config validates against the schema."""
    check_test_case_against_schema(TEST_CASES.by_path[test_case_name], ConfigSchema.OPTIMIZER)
    check_test_case_against_schema(TEST_CASES.by_path[test_case_name], ConfigSchema.UNIFIED)


@pytest.mark.parametrize("test_case_name", sorted(TEST_CASES.by_type["good"]))
def test_optimizer_configs_with_extra_param(test_case_name: str) -> None:
    """Checks that the optimizer config fails to validate if extra params are present in
    certain places.
    """
    check_test_case_config_with_extra_param(
        TEST_CASES.by_type["good"][test_case_name],
        ConfigSchema.OPTIMIZER,
    )
    check_test_case_config_with_extra_param(
        TEST_CASES.by_type["good"][test_case_name],
        ConfigSchema.UNIFIED,
    )
