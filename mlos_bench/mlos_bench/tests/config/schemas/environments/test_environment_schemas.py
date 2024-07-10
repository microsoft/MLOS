#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for environment schema validation."""

from os import path

import pytest

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.environments.base_environment import Environment
from mlos_bench.environments.composite_env import CompositeEnv
from mlos_bench.environments.script_env import ScriptEnv
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

NON_CONFIG_ENV_CLASSES = {
    # ScriptEnv is ABCMeta abstract, but there's no good way to test that
    # dynamically in Python.
    ScriptEnv,
}
expected_environment_class_names = [
    subclass.__module__ + "." + subclass.__name__
    for subclass in get_all_concrete_subclasses(Environment, pkg_name="mlos_bench")
    if subclass not in NON_CONFIG_ENV_CLASSES
]
assert expected_environment_class_names

COMPOSITE_ENV_CLASS_NAME = CompositeEnv.__module__ + "." + CompositeEnv.__name__
expected_leaf_environment_class_names = [
    subclass_name
    for subclass_name in expected_environment_class_names
    if subclass_name != COMPOSITE_ENV_CLASS_NAME
]


# Do the full cross product of all the test cases and all the Environment types.
@pytest.mark.parametrize("test_case_subtype", sorted(TEST_CASES.by_subtype))
@pytest.mark.parametrize("env_class", expected_environment_class_names)
def test_case_coverage_mlos_bench_environment_type(test_case_subtype: str, env_class: str) -> None:
    """Checks to see if there is a given type of test case for the given mlos_bench
    Environment type.
    """
    for test_case in TEST_CASES.by_subtype[test_case_subtype].values():
        if try_resolve_class_name(test_case.config.get("class")) == env_class:
            return
    raise NotImplementedError(
        f"Missing test case for subtype {test_case_subtype} for Environment class {env_class}"
    )


# Now we actually perform all of those validation tests.


@pytest.mark.parametrize("test_case_name", sorted(TEST_CASES.by_path))
def test_environment_configs_against_schema(test_case_name: str) -> None:
    """Checks that the environment config validates against the schema."""
    check_test_case_against_schema(TEST_CASES.by_path[test_case_name], ConfigSchema.ENVIRONMENT)
    check_test_case_against_schema(TEST_CASES.by_path[test_case_name], ConfigSchema.UNIFIED)


@pytest.mark.parametrize("test_case_name", sorted(TEST_CASES.by_type["good"]))
def test_environment_configs_with_extra_param(test_case_name: str) -> None:
    """Checks that the environment config fails to validate if extra params are present
    in certain places.
    """
    check_test_case_config_with_extra_param(
        TEST_CASES.by_type["good"][test_case_name],
        ConfigSchema.ENVIRONMENT,
    )
    check_test_case_config_with_extra_param(
        TEST_CASES.by_type["good"][test_case_name],
        ConfigSchema.UNIFIED,
    )
