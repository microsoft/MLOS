#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for empty tunable groups."""

from mlos_bench.tunables.tunable_groups import TunableGroups


def test_empty_tunable_group() -> None:
    """Test __nonzero__ property of tunable groups."""
    tunable_groups = TunableGroups(config={})
    assert not tunable_groups


def test_non_empty_tunable_group(tunable_groups: TunableGroups) -> None:
    """Test __nonzero__ property of tunable groups."""
    assert tunable_groups
