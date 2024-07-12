#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for accessing values to the individual parameters within tunable
groups.
"""

import pytest

from mlos_bench.tunables.covariant_group import CovariantTunableGroup
from mlos_bench.tunables.tunable import Tunable


def test_categorical_access_to_numerical_tunable(tunable_int: Tunable) -> None:
    """Make sure we throw an error on accessing a numerical tunable as a categorical."""
    with pytest.raises(ValueError):
        print(tunable_int.category)
    with pytest.raises(AssertionError):
        print(tunable_int.categories)


def test_numerical_access_to_categorical_tunable(tunable_categorical: Tunable) -> None:
    """Make sure we throw an error on accessing a numerical tunable as a categorical."""
    with pytest.raises(ValueError):
        print(tunable_categorical.numerical_value)
    with pytest.raises(AssertionError):
        print(tunable_categorical.range)


def test_covariant_group_repr(covariant_group: CovariantTunableGroup) -> None:
    """Tests that the covariant group representation works as expected."""
    assert repr(covariant_group).startswith(f"{covariant_group.name}:")


def test_covariant_group_tunables(covariant_group: CovariantTunableGroup) -> None:
    """Tests that we can access the tunables in the covariant group."""
    for tunable in covariant_group.get_tunables():
        assert isinstance(tunable, Tunable)
