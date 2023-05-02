#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for checking tunable definition rules.
"""

import pytest

from mlos_bench.tunables.tunable import Tunable


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
