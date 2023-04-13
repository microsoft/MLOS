#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for deep copy of tunable objects and groups.
"""

from mlos_bench.tunables.tunable import Tunable
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_copy_tunable_int(tunable_int: Tunable) -> None:
    """
    Check if deep copy works for Tunable object.
    """
    tunable_copy = tunable_int.copy()
    assert tunable_int == tunable_copy
    tunable_copy.value += 200
    assert tunable_int != tunable_copy


def test_copy_tunable_groups(tunable_groups: TunableGroups) -> None:
    """
    Check if deep copy works for TunableGroups object.
    """
    tunable_groups_copy = tunable_groups.copy()
    assert tunable_groups == tunable_groups_copy
    tunable_groups_copy["vmSize"] = "Standard_B2ms"
    assert tunable_groups_copy.is_updated()
    assert not tunable_groups.is_updated()
    assert tunable_groups != tunable_groups_copy
