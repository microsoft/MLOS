#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for schedulers schema validation."""

from os import path

import pytest

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.tests import try_resolve_class_name
from mlos_bench.tests.config.schemas import (
    check_test_case_against_schema,
    check_test_case_config_with_extra_param,
    get_schema_test_cases,
)
from mlos_core.tests import get_all_concrete_subclasses

# General testing strategy:
# - hand code a set of good/bad configs (useful to test editor schema checking)
# - enumerate and try to check that we've covered all the cases
# - for each config, load and validate against expected schema

TEST_CASES = get_schema_test_cases(path.join(path.dirname(__file__), "test-cases"))


# Dynamically enumerate some of the cases we want to make sure we cover.

expected_mlos_bench_scheduler_class_names = [
    subclass.__module__ + "." + subclass.__name__
    for subclass in get_all_concrete_subclasses(
        Scheduler,  # type: ignore[type-abstract]
        pkg_name="mlos_bench",
    )
]
assert expected_mlos_bench_scheduler_class_names

# Do the full cross product of all the test cases and all the scheduler types.


@pytest.mark.parametrize("test_case_subtype", sorted(TEST_CASES.by_subtype))
@pytest.mark.parametrize("mlos_bench_scheduler_type", expected_mlos_bench_scheduler_class_names)
def test_case_coverage_mlos_bench_scheduler_type(
    test_case_subtype: str,
    mlos_bench_scheduler_type: str,
) -> None:
    """Checks to see if there is a given type of test case for the given mlos_bench
    scheduler type.
    """
    for test_case in TEST_CASES.by_subtype[test_case_subtype].values():
        if try_resolve_class_name(test_case.config.get("class")) == mlos_bench_scheduler_type:
            return
    raise NotImplementedError(
        f"Missing test case for subtype {test_case_subtype} "
        f"for Scheduler class {mlos_bench_scheduler_type}"
    )


# Now we actually perform all of those validation tests.


@pytest.mark.parametrize("test_case_name", sorted(TEST_CASES.by_path))
def test_scheduler_configs_against_schema(test_case_name: str) -> None:
    """Checks that the scheduler config validates against the schema."""
    check_test_case_against_schema(TEST_CASES.by_path[test_case_name], ConfigSchema.SCHEDULER)
    check_test_case_against_schema(TEST_CASES.by_path[test_case_name], ConfigSchema.UNIFIED)


@pytest.mark.parametrize("test_case_name", sorted(TEST_CASES.by_type["good"]))
def test_scheduler_configs_with_extra_param(test_case_name: str) -> None:
    """Checks that the scheduler config fails to validate if extra params are present in
    certain places.
    """
    check_test_case_config_with_extra_param(
        TEST_CASES.by_type["good"][test_case_name],
        ConfigSchema.SCHEDULER,
    )
    check_test_case_config_with_extra_param(
        TEST_CASES.by_type["good"][test_case_name],
        ConfigSchema.UNIFIED,
    )


if __name__ == "__main__":
    pytest.main([__file__, "-n0"])
