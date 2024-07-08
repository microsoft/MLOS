#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for checking tunable comparisons."""

import pytest

from mlos_bench.tunables.covariant_group import CovariantTunableGroup
from mlos_bench.tunables.tunable import Tunable
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_tunable_int_value_lt(tunable_int: Tunable) -> None:
    """Tests that the __lt__ operator works as expected."""
    tunable_int_2 = tunable_int.copy()
    tunable_int_2.numerical_value += 1
    assert tunable_int.numerical_value < tunable_int_2.numerical_value
    assert tunable_int < tunable_int_2


def test_tunable_int_name_lt(tunable_int: Tunable) -> None:
    """Tests that the __lt__ operator works as expected."""
    tunable_int_2 = tunable_int.copy()
    tunable_int_2._name = "aaa"  # pylint: disable=protected-access
    assert tunable_int_2 < tunable_int


def test_tunable_categorical_value_lt(tunable_categorical: Tunable) -> None:
    """Tests that the __lt__ operator works as expected."""
    tunable_categorical_2 = tunable_categorical.copy()
    new_value = [
        x
        for x in tunable_categorical.categories
        if x != tunable_categorical.category and x is not None
    ][0]
    assert tunable_categorical.category is not None
    tunable_categorical_2.category = new_value
    if tunable_categorical.category < new_value:
        assert tunable_categorical < tunable_categorical_2
    elif tunable_categorical.category > new_value:
        assert tunable_categorical > tunable_categorical_2


def test_tunable_categorical_lt_null() -> None:
    """Tests that the __lt__ operator works as expected."""
    tunable_cat = Tunable(
        name="same-name",
        config={
            "type": "categorical",
            "values": ["floof", "fuzz"],
            "default": "floof",
        },
    )
    tunable_dog = Tunable(
        name="same-name",
        config={
            "type": "categorical",
            "values": [None, "doggo"],
            "default": None,
        },
    )
    assert tunable_dog < tunable_cat


def test_tunable_lt_same_name_different_type() -> None:
    """Tests that the __lt__ operator works as expected."""
    tunable_cat = Tunable(
        name="same-name",
        config={
            "type": "categorical",
            "values": ["floof", "fuzz"],
            "default": "floof",
        },
    )
    tunable_int = Tunable(
        name="same-name",
        config={
            "type": "int",
            "range": [1, 3],
            "default": 2,
        },
    )
    assert tunable_cat < tunable_int


def test_tunable_lt_different_object(tunable_int: Tunable) -> None:
    """Tests that the __lt__ operator works as expected."""
    assert (tunable_int < "foo") is False
    with pytest.raises(TypeError):
        assert "foo" < tunable_int  # type: ignore[operator]


def test_tunable_group_ne_object(tunable_groups: TunableGroups) -> None:
    """Tests that the __eq__ operator works as expected with other objects."""
    assert tunable_groups != "foo"


def test_covariant_group_ne_object(covariant_group: CovariantTunableGroup) -> None:
    """Tests that the __eq__ operator works as expected with other objects."""
    assert covariant_group != "foo"
