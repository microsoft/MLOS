#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for checking tunable parameters' distributions.
"""

import pytest

from mlos_bench.tunables.tunable import Tunable


def test_categorical_distribution() -> None:
    """
    Try to instantiate a categorical tunable with distribution specified.
    """
    with pytest.raises(ValueError):
        Tunable(name='test', config={
            "type": "categorical",
            "values": ["foo", "bar", "baz"],
            "distribution": {
                "type": "uniform"
            },
            "default": "foo"
        })


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_distribution_uniform(tunable_type: str) -> None:
    """
    Disallow null values param for numerical tunables.
    """
    tunable = Tunable(name="test", config={
        "type": tunable_type,
        "range": [0, 10],
        "distribution": {
            "type": "uniform"
        },
        "default": 0
    })
    assert tunable.is_numerical
    assert tunable.distribution == "uniform"
    assert not tunable.distribution_params


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_distribution_normal(tunable_type: str) -> None:
    """
    Disallow null values param for numerical tunables.
    """
    tunable = Tunable(name="test", config={
        "type": tunable_type,
        "range": [0, 10],
        "distribution": {
            "type": "normal",
            "params": {
                "mean": 0,
                "std": 1.0
            }
        },
        "default": 0
    })
    assert tunable.distribution == "normal"
    assert tunable.distribution_params == {"mean": 0, "std": 1.0}


@pytest.mark.parametrize("tunable_type", ["int", "float"])
def test_numerical_distribution_beta(tunable_type: str) -> None:
    """
    Disallow null values param for numerical tunables.
    """
    tunable = Tunable(name="test", config={
        "type": tunable_type,
        "range": [0, 10],
        "distribution": {
            "type": "beta",
            "params": {
                "a": 0.1,
                "b": 0.8
            }
        },
        "default": 0
    })
    assert tunable.distribution == "beta"
    assert tunable.distribution_params == {"a": 0.1, "b": 0.8}
