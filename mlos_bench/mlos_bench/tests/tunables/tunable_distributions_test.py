#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for checking tunable parameters' distributions."""

import json5 as json
import pytest

from mlos_bench.tunables.tunable import Tunable, TunableValueTypeName


def test_categorical_distribution() -> None:
    """Try to instantiate a categorical tunable with distribution specified."""
    with pytest.raises(ValueError):
        Tunable(
            name="test",
            config={
                "type": "categorical",
                "values": ["foo", "bar", "baz"],
                "distribution": {"type": "uniform"},
                "default": "foo",
            },
        )


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_distribution_uniform(tunable_type: TunableValueTypeName) -> None:
    """Create a numeric Tunable with explicit uniform distribution."""
    tunable = Tunable(
        name="test",
        config={
            "type": tunable_type,
            "range": [0, 10],
            "distribution": {"type": "uniform"},
            "default": 0,
        },
    )
    assert tunable.is_numerical
    assert tunable.distribution == "uniform"
    assert not tunable.distribution_params


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_distribution_normal(tunable_type: TunableValueTypeName) -> None:
    """Create a numeric Tunable with explicit Gaussian distribution specified."""
    tunable = Tunable(
        name="test",
        config={
            "type": tunable_type,
            "range": [0, 10],
            "distribution": {"type": "normal", "params": {"mu": 0, "sigma": 1.0}},
            "default": 0,
        },
    )
    assert tunable.distribution == "normal"
    assert tunable.distribution_params == {"mu": 0, "sigma": 1.0}


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_distribution_beta(tunable_type: TunableValueTypeName) -> None:
    """Create a numeric Tunable with explicit Beta distribution specified."""
    tunable = Tunable(
        name="test",
        config={
            "type": tunable_type,
            "range": [0, 10],
            "distribution": {"type": "beta", "params": {"alpha": 2, "beta": 5}},
            "default": 0,
        },
    )
    assert tunable.distribution == "beta"
    assert tunable.distribution_params == {"alpha": 2, "beta": 5}


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_distribution_unsupported(tunable_type: str) -> None:
    """Create a numeric Tunable with unsupported distribution."""
    json_config = f"""
    {{
        "type": "{tunable_type}",
        "range": [0, 10],
        "distribution": {{
            "type": "poisson",
            "params": {{
                "lambda": 1.0
            }}
        }},
        "default": 0
    }}
    """
    config = json.loads(json_config)
    with pytest.raises(ValueError):
        Tunable(name="test", config=config)
