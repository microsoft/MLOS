#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for checking the indexing rules for tunable groups."""

from mlos_bench.tunables.tunable import Tunable
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_tunable_group_indexing(
    tunable_groups: TunableGroups,
    tunable_categorical: Tunable,
) -> None:
    """Check that various types of indexing work for the tunable group."""
    # Check that the "in" operator works.
    assert tunable_categorical in tunable_groups
    assert tunable_categorical.name in tunable_groups

    # NOTE: we reassign the tunable_categorical here since they come from
    # different fixtures so are technically different objects.
    (tunable_categorical, covariant_group) = tunable_groups.get_tunable(tunable_categorical.name)
    assert tunable_groups.get_tunable(tunable_categorical)[0] == tunable_categorical

    assert tunable_categorical in covariant_group
    assert tunable_categorical.name in covariant_group

    # Check that we can lookup that tunable by name or tunable object in the covariant group.
    assert covariant_group.get_tunable(tunable_categorical) == tunable_categorical
    assert covariant_group.get_tunable(tunable_categorical.name) == tunable_categorical

    # Reset the value on the tunable using the tunable.
    tunable_categorical.value = tunable_categorical.default

    # Check that we can index by name or tunable object.
    assert tunable_groups[tunable_categorical] == tunable_categorical.value
    assert tunable_groups[tunable_categorical.name] == tunable_categorical.value
    assert covariant_group[tunable_categorical] == tunable_categorical.value
    assert covariant_group[tunable_categorical.name] == tunable_categorical.value

    # Check that we can assign a new value by index.
    new_value = [x for x in tunable_categorical.categories if x != tunable_categorical.value][0]
    tunable_groups[tunable_categorical] = new_value
    assert tunable_groups[tunable_categorical] == new_value
    assert tunable_groups[tunable_categorical.name] == new_value
    assert covariant_group[tunable_categorical] == new_value
    assert covariant_group[tunable_categorical.name] == new_value
    assert tunable_categorical.value == new_value
    assert tunable_categorical.value != tunable_categorical.default

    # Check that we can assign a new value by name.
    tunable_groups[tunable_categorical] = tunable_categorical.default
    assert tunable_categorical.value == tunable_categorical.default
    assert tunable_groups[tunable_categorical] == tunable_categorical.value
    assert tunable_groups[tunable_categorical.name] == tunable_categorical.value
    assert covariant_group[tunable_categorical] == tunable_categorical.value
    assert covariant_group[tunable_categorical.name] == tunable_categorical.value
