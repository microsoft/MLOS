#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for base environment class functionality."""

from typing import Dict

import pytest

from mlos_bench.environments.base_environment import Environment
from mlos_bench.tunables.tunable import TunableValue

_GROUPS = {
    "group": ["a", "b"],
    "list": ["c", "d"],
    "str": "efg",
    "empty": [],
    "other": ["h", "i", "j"],
}

# pylint: disable=protected-access


def test_expand_groups() -> None:
    """Check the dollar variable expansion for tunable groups."""
    assert Environment._expand_groups(
        [
            "begin",
            "$list",
            "$empty",
            "$str",
            "end",
        ],
        _GROUPS,
    ) == [
        "begin",
        "c",
        "d",
        "efg",
        "end",
    ]


def test_expand_groups_empty_input() -> None:
    """Make sure an empty group stays empty."""
    assert Environment._expand_groups([], _GROUPS) == []


def test_expand_groups_empty_list() -> None:
    """Make sure an empty group expansion works properly."""
    assert not Environment._expand_groups(["$empty"], _GROUPS)


def test_expand_groups_unknown() -> None:
    """Make sure we fail on unknown $GROUP names expansion."""
    with pytest.raises(KeyError):
        Environment._expand_groups(["$list", "$UNKNOWN", "$str", "end"], _GROUPS)


def test_expand_const_args() -> None:
    """Test expansion of const args via expand_vars."""
    const_args: Dict[str, TunableValue] = {
        "a": "b",
        "foo": "$bar/baz",
        "1": 1,
        "recursive": "$foo/expansion",
    }
    global_config: Dict[str, TunableValue] = {
        "bar": "blah",
    }
    result = Environment._expand_vars(const_args, global_config)
    assert result == {
        "a": "b",
        "foo": "blah/baz",
        "1": 1,
        "recursive": "blah/baz/expansion",
    }
