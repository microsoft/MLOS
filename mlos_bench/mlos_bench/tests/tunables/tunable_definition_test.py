#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for checking tunable definition rules.
"""

import json5 as json
import pytest

from mlos_bench.tunables.tunable import Tunable


def test_tunable_name() -> None:
    """
    Check that tunable name is valid.
    """
    with pytest.raises(ValueError):
        # ! characters are currently disallowed in tunable names
        Tunable(name='test!tunable', config={"type": "float", "range": [0, 1], "default": 0})


def test_categorical_required_params() -> None:
    """
    Check that required parameters are present for categorical tunables.
    """
    json_config = """
    {
        "type": "categorical",
        "values_missing": ["foo", "bar", "foo"],
        "default": "foo"
    }
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name='test', config=config)


def test_categorical_wrong_params() -> None:
    """
    Disallow range param for categorical tunables.
    """
    json_config = """
    {
        "type": "categorical",
        "values": ["foo", "bar", "foo"],
        "range": [0, 1],
        "default": "foo"
    }
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name='test', config=config)


def test_categorical_disallow_special_values() -> None:
    """
    Disallow special values for categorical values.
    """
    json_config = """
    {
        "type": "categorical",
        "values": ["foo", "bar", "foo"],
        "special": ["baz"],
        "default": "foo"
    }
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name='test', config=config)


def test_categorical_tunable_disallow_repeats() -> None:
    """
    Disallow duplicate values in categorical tunables.
    """
    with pytest.raises(ValueError):
        Tunable(name='test', config={
            "type": "categorical",
            "values": ["foo", "bar", "foo"],
            "default": "foo",
        })


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_tunable_disallow_null_default(tunable_type: str) -> None:
    """
    Disallow null values as default for numerical tunables.
    """
    with pytest.raises(ValueError):
        Tunable(name=f'test_{tunable_type}', config={
            "type": tunable_type,
            "range": [0, 10],
            "default": None,
        })


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_tunable_disallow_out_of_range(tunable_type: str) -> None:
    """
    Disallow out of range values as default for numerical tunables.
    """
    with pytest.raises(ValueError):
        Tunable(name=f'test_{tunable_type}', config={
            "type": tunable_type,
            "range": [0, 10],
            "default": 11,
        })


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_tunable_wrong_params(tunable_type: str) -> None:
    """
    Disallow values param for numerical tunables.
    """
    with pytest.raises(ValueError):
        Tunable(name=f'test_{tunable_type}', config={
            "type": tunable_type,
            "range": [0, 10],
            "values": ["foo", "bar"],
            "default": 0,
        })


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_tunable_required_params(tunable_type: str) -> None:
    """
    Disallow null values param for numerical tunables.
    """
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range_missing": [0, 10],
        "default": 0
    }}
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name=f'test_{tunable_type}', config=config)


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_tunable_invalid_range(tunable_type: str) -> None:
    """
    Disallow invalid range param for numerical tunables.
    """
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [0, 10, 7],
        "default": 0
    }}
    """
    config = json.loads(json_config)
    with pytest.raises(AssertionError):
        Tunable(name=f'test_{tunable_type}', config=config)


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_tunable_reversed_range(tunable_type: str) -> None:
    """
    Disallow reverse range param for numerical tunables.
    """
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [10, 0],
        "default": 0
    }}
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name=f'test_{tunable_type}', config=config)


def test_bad_type() -> None:
    """
    Disallow bad types.
    """
    json_config = """
    {
        "type": "foo",
        "range": [0, 10],
        "default": 0
    }
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name='test_bad_type', config=config)
