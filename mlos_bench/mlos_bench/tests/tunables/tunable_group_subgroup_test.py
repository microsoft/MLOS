#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for `TunableGroup.subgroup()` method."""

from mlos_bench.tunables.tunable_groups import TunableGroups


def test_tunable_group_subgroup(tunable_groups: TunableGroups) -> None:
    """Check that the subgroup() method returns only a selection of tunable
    parameters.
    """
    tunables = tunable_groups.subgroup(["provision"])
    assert tunables.get_param_values() == {"vmSize": "Standard_B4ms"}
