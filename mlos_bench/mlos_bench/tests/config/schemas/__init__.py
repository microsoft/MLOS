#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Common tests for config schemas and their validation and test cases."""

import os
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Set

import json5
import jsonschema
import pytest

from mlos_bench.config.schemas.config_schemas import ConfigSchema
from mlos_bench.tests.config import locate_config_examples


# A dataclass to make pylint happy.
@dataclass
class SchemaTestType:
    """The different type of schema test cases we expect to have."""

    test_case_type: str
    test_case_subtypes: Set[str]

    def __hash__(self) -> int:
        return hash(self.test_case_type)


# The different type of schema test cases we expect to have.
_SCHEMA_TEST_TYPES = {
    x.test_case_type: x
    for x in (
        SchemaTestType(test_case_type="good", test_case_subtypes={"full", "partial"}),
        SchemaTestType(test_case_type="bad", test_case_subtypes={"invalid", "unhandled"}),
    )
}


@dataclass
class SchemaTestCaseInfo:
    """Some basic info about a schema test case."""

    config: Dict[str, Any]
    test_case_file: str
    test_case_type: str
    test_case_subtype: str

    def __hash__(self) -> int:
        return hash(self.test_case_file)


def check_schema_dir_layout(test_cases_root: str) -> None:
    """Makes sure the directory layout matches what we expect so we aren't missing any
    extra configs or test cases.
    """
    for test_case_dir in os.listdir(test_cases_root):
        if test_case_dir == "README.md":
            continue
        if test_case_dir not in _SCHEMA_TEST_TYPES:
            raise NotImplementedError(f"Unhandled test case type: {test_case_dir}")
        for test_case_subdir in os.listdir(os.path.join(test_cases_root, test_case_dir)):
            if test_case_subdir == "README.md":
                continue
            if test_case_subdir not in _SCHEMA_TEST_TYPES[test_case_dir].test_case_subtypes:
                raise NotImplementedError(
                    f"Unhandled test case subtype {test_case_subdir} "
                    f"for test case type {test_case_dir}"
                )


@dataclass
class TestCases:
    """A container for test cases by type."""

    by_path: Dict[str, SchemaTestCaseInfo]
    by_type: Dict[str, Dict[str, SchemaTestCaseInfo]]
    by_subtype: Dict[str, Dict[str, SchemaTestCaseInfo]]


def get_schema_test_cases(test_cases_root: str) -> TestCases:
    """Gets a dict of schema test cases from the given root."""
    test_cases = TestCases(
        by_path={},
        by_type={x: {} for x in _SCHEMA_TEST_TYPES},
        by_subtype={
            y: {} for x in _SCHEMA_TEST_TYPES for y in _SCHEMA_TEST_TYPES[x].test_case_subtypes
        },
    )
    check_schema_dir_layout(test_cases_root)
    # Note: we sort the test cases so that we can deterministically test them in parallel.
    for test_case_type, schema_test_type in _SCHEMA_TEST_TYPES.items():
        for test_case_subtype in schema_test_type.test_case_subtypes:
            for test_case_file in locate_config_examples(
                test_cases_root, os.path.join(test_case_type, test_case_subtype)
            ):
                with open(test_case_file, mode="r", encoding="utf-8") as test_case_fh:
                    try:
                        test_case_info = SchemaTestCaseInfo(
                            config=json5.load(test_case_fh),
                            test_case_file=test_case_file,
                            test_case_type=test_case_type,
                            test_case_subtype=test_case_subtype,
                        )
                        test_cases.by_path[test_case_info.test_case_file] = test_case_info
                        test_cases.by_type[test_case_info.test_case_type][
                            test_case_info.test_case_file
                        ] = test_case_info
                        test_cases.by_subtype[test_case_info.test_case_subtype][
                            test_case_info.test_case_file
                        ] = test_case_info
                    except Exception as ex:
                        raise RuntimeError("Failed to load test case: " + test_case_file) from ex
    assert test_cases

    assert len(test_cases.by_type["good"]) > 0
    assert len(test_cases.by_type["bad"]) > 0
    assert len(test_cases.by_subtype) > 2

    return test_cases


def check_test_case_against_schema(
    test_case: SchemaTestCaseInfo,
    schema_type: ConfigSchema,
) -> None:
    """
    Checks the given test case against the given schema.

    Parameters
    ----------
    test_case : SchemaTestCaseInfo
        Schema test case to check.
    schema_type : ConfigSchema
        Schema to check against, e.g., ENVIRONMENT or SERVICE.

    Raises
    ------
    NotImplementedError
        If test case is not known.
    """
    if test_case.test_case_type == "good":
        schema_type.validate(test_case.config)
    elif test_case.test_case_type == "bad":
        with pytest.raises(jsonschema.ValidationError):
            schema_type.validate(test_case.config)
    else:
        raise NotImplementedError(f"Unknown test case type: {test_case.test_case_type}")


def check_test_case_config_with_extra_param(
    test_case: SchemaTestCaseInfo,
    schema_type: ConfigSchema,
) -> None:
    """Checks that the config fails to validate if extra params are present in certain
    places.
    """
    config = deepcopy(test_case.config)
    schema_type.validate(config)
    extra_outer_attr = "extra_outer_attr"
    config[extra_outer_attr] = "should not be here"
    with pytest.raises(jsonschema.ValidationError):
        schema_type.validate(config)
    del config[extra_outer_attr]
    if not config.get("config"):
        config["config"] = {}
    extra_config_attr = "extra_config_attr"
    config["config"][extra_config_attr] = "should not be here"
    with pytest.raises(jsonschema.ValidationError):
        schema_type.validate(config)
