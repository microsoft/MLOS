#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Common tests for config schemas and their validation and test cases.
"""

from dataclasses import dataclass
from typing import Any, Dict, Set, TypedDict

import os

import json5

from mlos_bench.tests.config import locate_config_examples


# The different type of schema test cases we expect to have.

@dataclass
class SchemaTestType:
    """
    The different type of schema test cases we expect to have.
    """

    test_case_type: str
    test_case_subtypes: Set[str]

    def __hash__(self) -> int:
        return hash(self.test_case_type)


# The different type of schema test cases we expect to have.
_SCHEMA_TEST_TYPES = dict((x.test_case_type, x) for x in (
    SchemaTestType(test_case_type='good', test_case_subtypes={'full', 'partial'}),
    SchemaTestType(test_case_type='bad', test_case_subtypes={'invalid', 'unhandled'}),
))

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


def check_schema_dir_layout(test_cases_root: str) -> None:
    """
    Makes sure the directory layout matches what we expect so we aren't missing
    any extra configs or test cases.
    """
    for test_case_dir in os.listdir(test_cases_root):
        if test_case_dir == 'README.md':
            continue
        if test_case_dir not in _SCHEMA_TEST_TYPES:
            raise NotImplementedError(f"Unhandled test case type: {test_case_dir}")
        for test_case_subdir in os.listdir(os.path.join(test_cases_root, test_case_dir)):
            if test_case_subdir == 'README.md':
                continue
            if test_case_subdir not in _SCHEMA_TEST_TYPES[test_case_dir].test_case_subtypes:
                raise NotImplementedError(f"Unhandled test case subtype {test_case_subdir} for test case type {test_case_dir}")


def get_schema_test_cases(test_cases_root: str) -> Dict[str, SchemaTestCaseInfo]:
    """
    Gets a dict of schema test cases from the given root.
    """
    test_cases: Dict[str, SchemaTestCaseInfo] = {}
    check_schema_dir_layout(test_cases_root)
    for (test_case_type, schema_test_type) in _SCHEMA_TEST_TYPES.items():
        for test_case_subtype in schema_test_type.test_case_subtypes:
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
