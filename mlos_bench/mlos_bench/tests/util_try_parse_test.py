#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for try_parse_val utility function."""

import math

from mlos_bench.util import try_parse_val


def test_try_parse_val() -> None:
    """Check that we can retrieve git info about the current repository correctly."""
    assert try_parse_val(None) is None
    assert try_parse_val("1") == int(1)
    assert try_parse_val("1.1") == float(1.1)
    assert try_parse_val("1e6") == float(1e6)
    res = try_parse_val("NaN")
    assert isinstance(res, float) and math.isnan(res)
    res = try_parse_val("inf")
    assert isinstance(res, float) and math.isinf(res)
    res = try_parse_val("-inf")
    assert isinstance(res, float) and math.isinf(res) and res < 0
    assert try_parse_val("str") == str("str")
