#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for storage schema validation."""

from os import path

import pytest

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tests import try_resolve_class_name
from mlos_bench.tests.config.schemas import (
    check_test_case_against_schema,
    check_test_case_config_with_extra_param,
    get_schema_test_cases,
)
from mlos_core.tests import get_all_concrete_subclasses

# General testing strategy:
# - hand code a set of good/bad configs (useful to test editor schema checking)
# - for each config, load and validate against expected schema

TEST_CASES = get_schema_test_cases(path.join(path.dirname(__file__), "test-cases"))

# Dynamically enumerate some of the cases we want to make sure we cover.

expected_mlos_bench_storage_class_names = [
    subclass.__module__ + "." + subclass.__name__
    for subclass in get_all_concrete_subclasses(
        Storage,  # type: ignore[type-abstract]
        pkg_name="mlos_bench",
    )
]
assert expected_mlos_bench_storage_class_names

# Do the full cross product of all the test cases and all the storage types.


@pytest.mark.parametrize("test_case_subtype", sorted(TEST_CASES.by_subtype))
@pytest.mark.parametrize("mlos_bench_storage_type", expected_mlos_bench_storage_class_names)
def test_case_coverage_mlos_bench_storage_type(
    test_case_subtype: str,
    mlos_bench_storage_type: str,
) -> None:
    """Checks to see if there is a given type of test case for the given mlos_bench
    storage type.
    """
    for test_case in TEST_CASES.by_subtype[test_case_subtype].values():
        if try_resolve_class_name(test_case.config.get("class")) == mlos_bench_storage_type:
            return
    raise NotImplementedError(
        f"Missing test case for subtype {test_case_subtype} "
        f"for Storage class {mlos_bench_storage_type}"
    )


# Now we actually perform all of those validation tests.


@pytest.mark.parametrize("test_case_name", sorted(TEST_CASES.by_path))
def test_storage_configs_against_schema(test_case_name: str) -> None:
    """Checks that the storage config validates against the schema."""
    check_test_case_against_schema(TEST_CASES.by_path[test_case_name], ConfigSchema.STORAGE)
    check_test_case_against_schema(TEST_CASES.by_path[test_case_name], ConfigSchema.UNIFIED)


@pytest.mark.parametrize("test_case_name", sorted(TEST_CASES.by_type["good"]))
def test_storage_configs_with_extra_param(test_case_name: str) -> None:
    """Checks that the storage config fails to validate if extra params are present in
    certain places.
    """
    check_test_case_config_with_extra_param(
        TEST_CASES.by_type["good"][test_case_name],
        ConfigSchema.STORAGE,
    )
    check_test_case_config_with_extra_param(
        TEST_CASES.by_type["good"][test_case_name],
        ConfigSchema.UNIFIED,
    )


if __name__ == "__main__":
    pytest.main(
        [__file__, "-n0"],
    )
