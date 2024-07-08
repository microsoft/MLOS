#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for tunable params schema validation."""

from os import path

import pytest

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.tests.config.schemas import (
    check_test_case_against_schema,
    get_schema_test_cases,
)

# General testing strategy:
# - hand code a set of good/bad configs (useful to test editor schema checking)
# - for each config, load and validate against expected schema

TEST_CASES = get_schema_test_cases(path.join(path.dirname(__file__), "test-cases"))


# Now we actually perform all of those validation tests.


@pytest.mark.parametrize("test_case_name", sorted(TEST_CASES.by_path))
def test_tunable_params_configs_against_schema(test_case_name: str) -> None:
    """Checks that the tunable params config validates against the schema."""
    check_test_case_against_schema(TEST_CASES.by_path[test_case_name], ConfigSchema.TUNABLE_PARAMS)
    check_test_case_against_schema(TEST_CASES.by_path[test_case_name], ConfigSchema.UNIFIED)
