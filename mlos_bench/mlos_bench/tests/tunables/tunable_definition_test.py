#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for checking tunable definition rules."""

import json5 as json
import pytest

from mlos_bench.tunables.tunable import Tunable, TunableValueTypeName


def test_tunable_name() -> None:
    """Check that tunable name is valid."""
    with pytest.raises(ValueError):
        # ! characters are currently disallowed in tunable names
        Tunable(name="test!tunable", config={"type": "float", "range": [0, 1], "default": 0})


def test_categorical_required_params() -> None:
    """Check that required parameters are present for categorical tunables."""
    json_config = """
    {
        "type": "categorical",
        "values_missing": ["foo", "bar", "baz"],
        "default": "foo"
    }
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name="test", config=config)


def test_categorical_weights() -> None:
    """Instantiate a categorical tunable with weights."""
    json_config = """
    {
        "type": "categorical",
        "values": ["foo", "bar", "baz"],
        "values_weights": [25, 25, 50],
        "default": "foo"
    }
    """
    config = json.loads(json_config)
    tunable = Tunable(name="test", config=config)
    assert tunable.weights == [25, 25, 50]


def test_categorical_weights_wrong_count() -> None:
    """Try to instantiate a categorical tunable with incorrect number of weights."""
    json_config = """
    {
        "type": "categorical",
        "values": ["foo", "bar", "baz"],
        "values_weights": [50, 50],
        "default": "foo"
    }
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name="test", config=config)


def test_categorical_weights_wrong_values() -> None:
    """Try to instantiate a categorical tunable with invalid weights."""
    json_config = """
    {
        "type": "categorical",
        "values": ["foo", "bar", "baz"],
        "values_weights": [-1, 50, 50],
        "default": "foo"
    }
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name="test", config=config)


def test_categorical_wrong_params() -> None:
    """Disallow range param for categorical tunables."""
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
        Tunable(name="test", config=config)


def test_categorical_disallow_special_values() -> None:
    """Disallow special values for categorical values."""
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
        Tunable(name="test", config=config)


def test_categorical_tunable_disallow_repeats() -> None:
    """Disallow duplicate values in categorical tunables."""
    with pytest.raises(ValueError):
        Tunable(
            name="test",
            config={
                "type": "categorical",
                "values": ["foo", "bar", "foo"],
                "default": "foo",
            },
        )


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_tunable_disallow_null_default(tunable_type: TunableValueTypeName) -> None:
    """Disallow null values as default for numerical tunables."""
    with pytest.raises(ValueError):
        Tunable(
            name=f"test_{tunable_type}",
            config={
                "type": tunable_type,
                "range": [0, 10],
                "default": None,
            },
        )


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_tunable_disallow_out_of_range(tunable_type: TunableValueTypeName) -> None:
    """Disallow out of range values as default for numerical tunables."""
    with pytest.raises(ValueError):
        Tunable(
            name=f"test_{tunable_type}",
            config={
                "type": tunable_type,
                "range": [0, 10],
                "default": 11,
            },
        )


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_tunable_wrong_params(tunable_type: TunableValueTypeName) -> None:
    """Disallow values param for numerical tunables."""
    with pytest.raises(ValueError):
        Tunable(
            name=f"test_{tunable_type}",
            config={
                "type": tunable_type,
                "range": [0, 10],
                "values": ["foo", "bar"],
                "default": 0,
            },
        )


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_tunable_required_params(tunable_type: TunableValueTypeName) -> None:
    """Disallow null values param for numerical tunables."""
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range_missing": [0, 10],
        "default": 0
    }}
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name=f"test_{tunable_type}", config=config)


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_tunable_invalid_range(tunable_type: TunableValueTypeName) -> None:
    """Disallow invalid range param for numerical tunables."""
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [0, 10, 7],
        "default": 0
    }}
    """
    config = json.loads(json_config)
    with pytest.raises(AssertionError):
        Tunable(name=f"test_{tunable_type}", config=config)


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_tunable_reversed_range(tunable_type: TunableValueTypeName) -> None:
    """Disallow reverse range param for numerical tunables."""
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [10, 0],
        "default": 0
    }}
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name=f"test_{tunable_type}", config=config)


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_weights(tunable_type: TunableValueTypeName) -> None:
    """Instantiate a numerical tunable with weighted special values."""
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [0, 100],
        "special": [0],
        "special_weights": [0.1],
        "range_weight": 0.9,
        "default": 0
    }}
    """
    config = json.loads(json_config)
    tunable = Tunable(name="test", config=config)
    assert tunable.special == [0]
    assert tunable.weights == [0.1]
    assert tunable.range_weight == 0.9


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_quantization(tunable_type: TunableValueTypeName) -> None:
    """Instantiate a numerical tunable with quantization."""
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [0, 100],
        "quantization": 10,
        "default": 0
    }}
    """
    config = json.loads(json_config)
    tunable = Tunable(name="test", config=config)
    assert tunable.quantization == 10
    assert not tunable.is_log


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_log(tunable_type: TunableValueTypeName) -> None:
    """Instantiate a numerical tunable with log scale."""
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [0, 100],
        "log": true,
        "default": 0
    }}
    """
    config = json.loads(json_config)
    tunable = Tunable(name="test", config=config)
    assert tunable.is_log


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_weights_no_specials(tunable_type: TunableValueTypeName) -> None:
    """Raise an error if special_weights are specified but no special values."""
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [0, 100],
        "special_weights": [0.1, 0.9],
        "default": 0
    }}
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name="test", config=config)


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_weights_non_normalized(tunable_type: TunableValueTypeName) -> None:
    """Instantiate a numerical tunable with non-normalized weights of the special
    values.
    """
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [0, 100],
        "special": [-1, 0],
        "special_weights": [0, 10],
        "range_weight": 90,
        "default": 0
    }}
    """
    config = json.loads(json_config)
    tunable = Tunable(name="test", config=config)
    assert tunable.special == [-1, 0]
    assert tunable.weights == [0, 10]  # Zero weights are ok
    assert tunable.range_weight == 90


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_weights_wrong_count(tunable_type: TunableValueTypeName) -> None:
    """Try to instantiate a numerical tunable with incorrect number of weights."""
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [0, 100],
        "special": [0],
        "special_weights": [0.1, 0.1, 0.8],
        "range_weight": 0.1,
        "default": 0
    }}
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name="test", config=config)


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_weights_no_range_weight(tunable_type: TunableValueTypeName) -> None:
    """Try to instantiate a numerical tunable with weights but no range_weight."""
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [0, 100],
        "special": [0, -1],
        "special_weights": [0.1, 0.2],
        "default": 0
    }}
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name="test", config=config)


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_range_weight_no_weights(tunable_type: TunableValueTypeName) -> None:
    """Try to instantiate a numerical tunable with specials but no range_weight."""
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [0, 100],
        "special": [0, -1],
        "range_weight": 0.3,
        "default": 0
    }}
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name="test", config=config)


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_range_weight_no_specials(tunable_type: TunableValueTypeName) -> None:
    """Try to instantiate a numerical tunable with specials but no range_weight."""
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [0, 100],
        "range_weight": 0.3,
        "default": 0
    }}
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name="test", config=config)


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_weights_wrong_values(tunable_type: TunableValueTypeName) -> None:
    """Try to instantiate a numerical tunable with incorrect number of weights."""
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [0, 100],
        "special": [0],
        "special_weights": [-1],
        "range_weight": 10,
        "default": 0
    }}
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name="test", config=config)


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_quantization_wrong(tunable_type: TunableValueTypeName) -> None:
    """Instantiate a numerical tunable with invalid number of quantization points."""
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [0, 100],
        "quantization": 0,
        "default": 0
    }}
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name="test", config=config)


def test_bad_type() -> None:
    """Disallow bad types."""
    json_config = """
    {
        "type": "foo",
        "range": [0, 10],
        "default": 0
    }
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name="test_bad_type", config=config)
