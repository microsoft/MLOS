#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for tunable params schema validation.
"""

from os import path
from typing import Dict

import jsonschema
import pytest

from mlos_bench.config.schemas import ConfigSchema

from mlos_bench.tests.config.schemas import get_schema_test_cases, SchemaTestCaseInfo


# General testing strategy:
# - hand code a set of good/bad configs (useful to test editor schema checking)
# - for each config, load and validate against expected schema

TEST_CASES: Dict[str, SchemaTestCaseInfo] = get_schema_test_cases(path.join(path.dirname(__file__), "test-cases"))
TEST_CASES_BY_TYPE: Dict[str, Dict[str, SchemaTestCaseInfo]] = {}
TEST_CASES_BY_SUBTYPE: Dict[str, Dict[str, SchemaTestCaseInfo]] = {}
for test_case_info in TEST_CASES.values():
    TEST_CASES_BY_TYPE.setdefault(test_case_info["test_case_type"], {})
    TEST_CASES_BY_TYPE[test_case_info["test_case_type"]][test_case_info["test_case"]] = test_case_info
    TEST_CASES_BY_SUBTYPE.setdefault(test_case_info["test_case_subtype"], {})
    TEST_CASES_BY_SUBTYPE[test_case_info["test_case_subtype"]][test_case_info["test_case"]] = test_case_info

assert len(TEST_CASES_BY_TYPE["good"]) > 0
assert len(TEST_CASES_BY_TYPE["bad"]) > 0
assert len(TEST_CASES_BY_SUBTYPE) > 2


# Now we actually perform all of those validation tests.

@pytest.mark.parametrize("test_case_name", list(TEST_CASES.keys()))
def test_tunable_params_configs_against_schema(test_case_name: str) -> None:
    """
    Checks that the tunable params config validates against the schema.
    """
    test_case = TEST_CASES[test_case_name]
    if test_case["test_case_type"] == "good":
        ConfigSchema.TUNABLE_PARAMS.validate(test_case["config"])
    elif test_case["test_case_type"] == "bad":
        with pytest.raises((jsonschema.ValidationError, jsonschema.SchemaError)):
            ConfigSchema.TUNABLE_PARAMS.validate(test_case["config"])
    else:
        raise NotImplementedError(f"Unknown test case type: {test_case['test_case_type']}")
