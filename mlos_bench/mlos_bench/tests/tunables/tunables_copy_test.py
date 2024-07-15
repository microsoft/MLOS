#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for deep copy of tunable objects and groups."""

from mlos_bench.tunables.covariant_group import CovariantTunableGroup
from mlos_bench.tunables.tunable import Tunable, TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_copy_tunable_int(tunable_int: Tunable) -> None:
    """Check if deep copy works for Tunable object."""
    tunable_copy = tunable_int.copy()
    assert tunable_int == tunable_copy
    tunable_copy.numerical_value += 200
    assert tunable_int != tunable_copy


def test_copy_tunable_groups(tunable_groups: TunableGroups) -> None:
    """Check if deep copy works for TunableGroups object."""
    tunable_groups_copy = tunable_groups.copy()
    assert tunable_groups == tunable_groups_copy
    tunable_groups_copy["vmSize"] = "Standard_B2ms"
    assert tunable_groups_copy.is_updated()
    assert not tunable_groups.is_updated()
    assert tunable_groups != tunable_groups_copy


def test_copy_covariant_group(covariant_group: CovariantTunableGroup) -> None:
    """Check if deep copy works for TunableGroups object."""
    covariant_group_copy = covariant_group.copy()
    assert covariant_group == covariant_group_copy
    tunable = next(iter(covariant_group.get_tunables()))
    new_value: TunableValue
    if tunable.is_categorical:
        new_value = [x for x in tunable.categories if x != tunable.category][0]
    elif tunable.is_numerical:
        new_value = tunable.numerical_value + 1
    covariant_group_copy[tunable] = new_value
    assert covariant_group_copy.is_updated()
    assert not covariant_group.is_updated()
    assert covariant_group != covariant_group_copy
