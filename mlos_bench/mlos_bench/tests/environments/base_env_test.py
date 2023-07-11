#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for base environment class functionality.
"""

import pytest

from mlos_bench.environments.base_environment import Environment

_GROUPS = {
    "group": ["a", "b"],
    "list": ["c", "d"],
    "str": "efg",
    "empty": [],
    "other": ["h", "i", "j"],
}

# pylint: disable=protected-access


def test_expand_groups() -> None:
    """
    Check the dollar variable expansion for tunable groups.
    """
    assert Environment._expand_groups(
        ["begin", "$list", "$empty", "$str", "end"],
        _GROUPS) == ["begin", "c", "d", "efg", "end"]


def test_expand_groups_empty_input() -> None:
    """
    Make sure an empty group stays empty.
    """
    assert Environment._expand_groups([], _GROUPS) == []


def test_expand_groups_empty_list() -> None:
    """
    Make sure an empty group expansion works properly.
    """
    assert not Environment._expand_groups(["$empty"], _GROUPS)


def test_expand_groups_unknown() -> None:
    """
    Make sure we fail on unknown $GROUP names expansion.
    """
    with pytest.raises(KeyError):
        Environment._expand_groups(["$list", "$UNKNOWN", "$str", "end"], _GROUPS)
