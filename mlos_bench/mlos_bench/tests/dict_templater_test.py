#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for DictTemplater class."""

from copy import deepcopy
from typing import Any, Dict

import pytest

from mlos_bench.dict_templater import DictTemplater
from mlos_bench.os_environ import environ


@pytest.fixture
def source_template_dict() -> Dict[str, Any]:
    """A source dictionary with template variables."""
    return {
        "extra_str-ref": "$extra_str-ref",
        "str": "string",
        "str_ref": "$str-ref",
        "secondary_expansion": "${str_ref}",
        "tertiary_expansion": "$secondary_expansion",
        "int": 1,
        "int_ref": "$int-ref",
        "float": 1.0,
        "float_ref": "$float-ref",
        "bool": True,
        "bool_ref": "$bool-ref",
        "list": [
            "$str",
            "$int",
            "$float",
        ],
        "dict": {
            "nested-str-ref": "nested-$str-ref",
            "nested-extra-str-ref": "nested-$extra_str-ref",
        },
    }


# pylint: disable=redefined-outer-name


def test_no_side_effects(source_template_dict: Dict[str, Any]) -> None:
    """Test that the templater does not modify the source dictionary."""
    source_template_dict_copy = deepcopy(source_template_dict)
    results = DictTemplater(source_template_dict_copy).expand_vars()
    assert results
    assert source_template_dict_copy == source_template_dict


def test_secondary_expansion(source_template_dict: Dict[str, Any]) -> None:
    """Test that internal expansions work as expected."""
    results = DictTemplater(source_template_dict).expand_vars()
    assert results == {
        "extra_str-ref": "$extra_str-ref",
        "str": "string",
        "str_ref": "string-ref",
        "secondary_expansion": "string-ref",
        "tertiary_expansion": "string-ref",
        "int": 1,
        "int_ref": "1-ref",
        "float": 1.0,
        "float_ref": "1.0-ref",
        "bool": True,
        "bool_ref": "True-ref",
        "list": [
            "string",
            "1",
            "1.0",
        ],
        "dict": {
            "nested-str-ref": "nested-string-ref",
            "nested-extra-str-ref": "nested-$extra_str-ref",
        },
    }


def test_os_env_expansion(source_template_dict: Dict[str, Any]) -> None:
    """Test that expansions from OS env work as expected."""
    environ["extra_str"] = "os-env-extra_str"
    environ["string"] = "shouldn't be used"

    results = DictTemplater(source_template_dict).expand_vars(use_os_env=True)
    assert results == {
        "extra_str-ref": f"{environ['extra_str']}-ref",
        "str": "string",
        "str_ref": "string-ref",
        "secondary_expansion": "string-ref",
        "tertiary_expansion": "string-ref",
        "int": 1,
        "int_ref": "1-ref",
        "float": 1.0,
        "float_ref": "1.0-ref",
        "bool": True,
        "bool_ref": "True-ref",
        "list": [
            "string",
            "1",
            "1.0",
        ],
        "dict": {
            "nested-str-ref": "nested-string-ref",
            "nested-extra-str-ref": f"nested-{environ['extra_str']}-ref",
        },
    }


def test_from_extras_expansion(source_template_dict: Dict[str, Any]) -> None:
    """Test that."""
    extra_source_dict = {
        "extra_str": "str-from-extras",
        "string": "shouldn't be used",
    }
    results = DictTemplater(source_template_dict).expand_vars(extra_source_dict=extra_source_dict)
    assert results == {
        "extra_str-ref": f"{extra_source_dict['extra_str']}-ref",
        "str": "string",
        "str_ref": "string-ref",
        "secondary_expansion": "string-ref",
        "tertiary_expansion": "string-ref",
        "int": 1,
        "int_ref": "1-ref",
        "float": 1.0,
        "float_ref": "1.0-ref",
        "bool": True,
        "bool_ref": "True-ref",
        "list": [
            "string",
            "1",
            "1.0",
        ],
        "dict": {
            "nested-str-ref": "nested-string-ref",
            "nested-extra-str-ref": f"nested-{extra_source_dict['extra_str']}-ref",
        },
    }
