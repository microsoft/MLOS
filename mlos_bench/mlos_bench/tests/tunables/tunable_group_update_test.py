#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for checking the is_updated flag for tunable groups."""

from mlos_bench.tunables.tunable_groups import TunableGroups

_TUNABLE_VALUES = {
    "kernel_sched_migration_cost_ns": 8888,
    "kernel_sched_latency_ns": 9999,
}


def test_tunable_group_update(tunable_groups: TunableGroups) -> None:
    """Test that updating a tunable group raises the is_updated flag."""
    tunable_groups.assign(_TUNABLE_VALUES)
    assert tunable_groups.is_updated()


def test_tunable_group_update_twice(tunable_groups: TunableGroups) -> None:
    """Test that updating a tunable group with the same values do *NOT* raises the
    is_updated flag.
    """
    tunable_groups.assign(_TUNABLE_VALUES)
    assert tunable_groups.is_updated()

    tunable_groups.reset()
    assert not tunable_groups.is_updated()

    tunable_groups.assign(_TUNABLE_VALUES)
    assert not tunable_groups.is_updated()


def test_tunable_group_update_kernel(tunable_groups: TunableGroups) -> None:
    """Test that the is_updated flag is set only for the affected covariant group."""
    tunable_groups.assign(_TUNABLE_VALUES)
    assert tunable_groups.is_updated()
    assert tunable_groups.is_updated(["kernel"])
    assert not tunable_groups.is_updated(["boot", "provision"])


def test_tunable_group_update_boot(tunable_groups: TunableGroups) -> None:
    """Test that the is_updated flag is set only for the affected covariant group."""
    tunable_groups.assign(_TUNABLE_VALUES)
    assert tunable_groups.is_updated()
    assert not tunable_groups.is_updated(["boot"])

    tunable_groups.reset()
    tunable_groups["idle"] = "mwait"
    assert tunable_groups.is_updated()
    assert tunable_groups.is_updated(["boot"])
    assert not tunable_groups.is_updated(["kernel"])
