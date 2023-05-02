#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for unique references to tunables when they're loaded multiple times.
"""

import pytest

from mlos_bench.tunables.tunable_groups import TunableGroups


def test_merging_tunable_groups(tunable_groups_config: dict) -> None:
    """
    Check that the merging logic of tunable groups works as expected.
    """
    parent_tunables = TunableGroups(tunable_groups_config)

    # Pretend we loaded this one from disk another time.
    tunables_dup = TunableGroups(tunable_groups_config)

    (tunable, covariant_group) = next(iter(parent_tunables))
    (tunable_dup, covariant_group_dup) = next(iter(tunables_dup))

    assert tunable == tunable_dup
    assert covariant_group == covariant_group_dup

    # Test merging prior to making any changes.
    parent_tunable_copy = parent_tunables.copy()
    parent_tunables = parent_tunables.merge(tunables_dup)

    # Check that they're the same.
    assert covariant_group == covariant_group_dup
    assert parent_tunables == tunables_dup
    assert parent_tunables == parent_tunable_copy

    (tunable_retry, covariant_group_retry) = next(iter(parent_tunables))
    assert tunable == tunable_retry
    assert covariant_group == covariant_group_retry

    # Update a value to indicate that they're separate copies.
    if tunable.is_categorical:
        tunable.categorical_value = [x for x in tunable.categorical_values if x != tunable.categorical_value][0]
    elif tunable.is_numerical:
        tunable.numerical_value += 1

    # Check that they're separate.
    assert tunable != tunable_dup
    assert covariant_group != covariant_group_dup
    assert parent_tunables != tunables_dup

    # Try merging again (should be disallowed).
    parent_tunable_copy = parent_tunables.copy()
    with pytest.raises(AssertionError):
        parent_tunables = parent_tunables.merge(tunables_dup)

    assert tunable != tunable_dup
    assert covariant_group != covariant_group_dup
    assert parent_tunables != tunables_dup
    assert parent_tunables == parent_tunable_copy
