#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for unique references to tunables when they're loaded multiple times."""

import json5 as json
import pytest

from mlos_bench.tunables.tunable_groups import TunableGroups


def test_duplicate_merging_tunable_groups(tunable_groups_config: dict) -> None:
    """Check that the merging logic of tunable groups works as expected."""
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
        tunable.category = [x for x in tunable.categories if x != tunable.category][0]
    elif tunable.is_numerical:
        tunable.numerical_value += 1

    # Check that they're separate.
    assert tunable != tunable_dup
    assert covariant_group != covariant_group_dup
    assert parent_tunables != tunables_dup

    # Should be ok since we only changed the value.
    parent_tunable_copy = parent_tunables.copy()
    parent_tunables = parent_tunables.merge(tunables_dup)

    # Make sure nothing changed in the parent.
    assert tunable != tunable_dup
    assert covariant_group != covariant_group_dup
    assert parent_tunables != tunables_dup
    assert parent_tunables == parent_tunable_copy


def test_overlapping_group_merge_tunable_groups(tunable_groups_config: dict) -> None:
    """Check that the merging logic of tunable groups works as expected."""
    parent_tunables = TunableGroups(tunable_groups_config)

    # This config should overlap with the parent config.
    # (same group name, different param name, different values)
    other_tunables_json = """
    {
        "boot": {
            "cost": 300,
            "params": {
                "noidle": {
                    "description": "(different) idling method",
                    "type": "categorical",
                    "default": "nomwait",
                    "values": ["nohalt", "nomwait", "idle"]
                }
            }
        }
    }
    """

    other_tunables_config = json.loads(other_tunables_json)
    other_tunables = TunableGroups(other_tunables_config)

    with pytest.raises(ValueError):
        parent_tunables.merge(other_tunables)


def test_bad_extended_merge_tunable_group(tunable_groups_config: dict) -> None:
    """Check that the merging logic of tunable groups works as expected."""
    parent_tunables = TunableGroups(tunable_groups_config)

    # This config should overlap with the parent config.
    # (different group name, same param name)
    other_tunables_json = """
    {
        "new-group": {
            "cost": 300,
            "params": {
                "idle": {
                    "type": "categorical",
                    "description": "Idling method",
                    "default": "mwait",
                    "values": ["halt", "mwait", "noidle"]
                }
            }
        }
    }
    """

    other_tunables_config = json.loads(other_tunables_json)
    other_tunables = TunableGroups(other_tunables_config)

    with pytest.raises(ValueError):
        parent_tunables.merge(other_tunables)


def test_good_extended_merge_tunable_group(tunable_groups_config: dict) -> None:
    """Check that the merging logic of tunable groups works as expected."""
    parent_tunables = TunableGroups(tunable_groups_config)

    # This config should overlap with the parent config.
    # (different group name, same param name)
    other_tunables_json = """
    {
        "new-group": {
            "cost": 300,
            "params": {
                "new-param": {
                    "type": "int",
                    "default": 0,
                    "range": [0, 10]
                }
            }
        }
    }
    """

    other_tunables_config = json.loads(other_tunables_json)
    other_tunables = TunableGroups(other_tunables_config)

    assert "new-param" not in parent_tunables
    assert "new-param" in other_tunables

    parent_tunables = parent_tunables.merge(other_tunables)

    assert "new-param" in parent_tunables
    (tunable_param, covariant_group) = parent_tunables.get_tunable("new-param")
    assert tunable_param.name == "new-param"
    assert covariant_group.name == "new-group"
