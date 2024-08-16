#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for checking tunable size properties."""

import numpy as np
import pytest

from mlos_bench.tunables.tunable import Tunable

# Note: these test do *not* check the ConfigSpace conversions for those same Tunables.
# That is checked indirectly via grid_search_optimizer_test.py


def test_tunable_int_size_props() -> None:
    """Test tunable int size properties."""
    tunable = Tunable(
        name="test",
        config={
            "type": "int",
            "range": [1, 5],
            "default": 3,
        },
    )
    assert tunable.span == 4
    assert tunable.cardinality == 5
    expected = [1, 2, 3, 4, 5]
    assert list(tunable.quantized_values or []) == expected
    assert list(tunable.values or []) == expected


def test_tunable_float_size_props() -> None:
    """Test tunable float size properties."""
    tunable = Tunable(
        name="test",
        config={
            "type": "float",
            "range": [1.5, 5],
            "default": 3,
        },
    )
    assert tunable.span == 3.5
    assert tunable.cardinality == np.inf
    assert tunable.quantized_values is None
    assert tunable.values is None


def test_tunable_categorical_size_props() -> None:
    """Test tunable categorical size properties."""
    tunable = Tunable(
        name="test",
        config={
            "type": "categorical",
            "values": ["a", "b", "c"],
            "default": "a",
        },
    )
    with pytest.raises(AssertionError):
        _ = tunable.span
    assert tunable.cardinality == 3
    assert tunable.values == ["a", "b", "c"]
    with pytest.raises(AssertionError):
        _ = tunable.quantized_values


def test_tunable_quantized_int_size_props() -> None:
    """Test quantized tunable int size properties."""
    tunable = Tunable(
        name="test",
        config={"type": "int", "range": [100, 1000], "default": 100, "quantization": 100},
    )
    assert tunable.span == 900
    assert tunable.cardinality == 10
    expected = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    assert list(tunable.quantized_values or []) == expected
    assert list(tunable.values or []) == expected


def test_tunable_quantized_float_size_props() -> None:
    """Test quantized tunable float size properties."""
    tunable = Tunable(
        name="test",
        config={"type": "float", "range": [0, 1], "default": 0, "quantization": 0.1},
    )
    assert tunable.span == 1
    assert tunable.cardinality == 11
    expected = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    assert pytest.approx(list(tunable.quantized_values or []), 0.0001) == expected
    assert pytest.approx(list(tunable.values or []), 0.0001) == expected
