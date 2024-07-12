#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for `nullable` utility function."""
import pytest

from mlos_bench.util import nullable


def test_nullable_str() -> None:
    """Check that the `nullable` function works properly for `str`."""
    assert nullable(str, None) is None
    assert nullable(str, "") is not None
    assert nullable(str, "") == ""
    assert nullable(str, "test") == "test"
    assert nullable(str, 10) == "10"


def test_nullable_int() -> None:
    """Check that the `nullable` function works properly for `int`."""
    assert nullable(int, None) is None
    assert nullable(int, 10) is not None
    assert nullable(int, 10) == 10
    assert nullable(int, 36.6) == 36


def test_nullable_func() -> None:
    """Check that the `nullable` function works properly with `list.pop()` function."""
    assert nullable(list.pop, None) is None
    assert nullable(list.pop, [1, 2, 3]) == 3

    with pytest.raises(IndexError):
        assert nullable(list.pop, [])
