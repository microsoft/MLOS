#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Common tests for config schemas and their validation and test cases.
"""

from typing import Any, Dict, TypedDict

from glob import glob
import os

import json5

from mlos_bench.tests.config import locate_config_examples


# The different type of schema test cases we expect to have.
SCHEMA_TEST_TYPES = {
    "good": [
        "full",
        "partial",
    ],
    "bad": [
        "invalid",
        "unhandled",
    ],
}

# Some attributes we don't expect to be in any schema.
# Used for dynamically check that we've covered all cases.
EXTRA_OUTER_ATTR = "extra_outer_attr"
EXTRA_CONFIG_ATTR = "extra_config_attr"


class SchemaTestCaseInfo(TypedDict):
    """
    Some basic info about a schema test case.
    """

    config: Dict[str, Any]
    test_case: str
    test_case_type: str
    test_case_subtype: str


def get_schema_test_cases(test_cases_root: str) -> Dict[str, SchemaTestCaseInfo]:
    """
    Gets a dict of schema test cases from the given root.
    """
    test_cases: Dict[str, SchemaTestCaseInfo] = {}
    for subdir in os.listdir(test_cases_root):
        if subdir == 'README.md':
            continue
        if subdir not in SCHEMA_TEST_TYPES:
            raise NotImplementedError("Unhandled test case type: " + subdir)
    for test_case_type, test_case_subtypes in SCHEMA_TEST_TYPES.items():
        for subdir in os.listdir(os.path.join(test_cases_root, test_case_type)):
            if subdir == 'README.md':
                continue
            if subdir not in test_case_subtypes:
                raise NotImplementedError("Unhandled test case subtype: " + subdir)
        for test_case_subtype in test_case_subtypes:
            for test_case in locate_config_examples(os.path.join(test_cases_root, test_case_type, test_case_subtype)):
                with open(test_case, mode='r', encoding='utf-8') as test_case_fh:
                    try:
                        test_cases[test_case] = SchemaTestCaseInfo({
                            "config": json5.load(test_case_fh),
                            "test_case": test_case,
                            "test_case_type": test_case_type,
                            "test_case_subtype": test_case_subtype,
                        })
                    except Exception as ex:
                        raise RuntimeError("Failed to load test case: " + test_case) from ex
    # assert test_case_infos
    return test_cases
