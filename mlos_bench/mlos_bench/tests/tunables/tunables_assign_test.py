#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for assigning values to the individual parameters within tunable groups.
"""

import pytest

from mlos_bench.tunables.tunable import Tunable
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_tunables_assign_unknown_param(tunable_groups: TunableGroups) -> None:
    """
    Make sure that bulk assignment fails for parameters
    that don't exist in the TunableGroups object.
    """
    with pytest.raises(KeyError):
        tunable_groups.assign({
            "vmSize": "Standard_B2ms",
            "rootfs": "ext4",
            "UnknownParam_1": 1,
            "UnknownParam_2": "invalid-value"
        })


def test_tunables_assign_invalid_categorical(tunable_groups: TunableGroups) -> None:
    """
    Check parameter validation for categorical tunables.
    """
    with pytest.raises(ValueError):
        tunable_groups.assign({"vmSize": "InvalidSize"})


def test_tunables_assign_invalid_range(tunable_groups: TunableGroups) -> None:
    """
    Check parameter out-of-range validation for numerical tunables.
    """
    with pytest.raises(ValueError):
        tunable_groups.assign({"kernel_sched_migration_cost_ns": -2})


def test_tunables_assign_coerce_str(tunable_groups: TunableGroups) -> None:
    """
    Check the conversion from strings when assigning to an integer parameter.
    """
    tunable_groups.assign({"kernel_sched_migration_cost_ns": "10000"})


def test_tunables_assign_coerce_str_range_check(tunable_groups: TunableGroups) -> None:
    """
    Check the range when assigning to an integer tunable.
    """
    with pytest.raises(ValueError):
        tunable_groups.assign({"kernel_sched_migration_cost_ns": "5500000"})


def test_tunables_assign_coerce_str_invalid(tunable_groups: TunableGroups) -> None:
    """
    Make sure we fail when assigning an invalid string to an integer tunable.
    """
    with pytest.raises(ValueError):
        tunable_groups.assign({"kernel_sched_migration_cost_ns": "1.1"})


def test_tunable_assign_str_to_int(tunable_int: Tunable) -> None:
    """
    Check str to int coercion.
    """
    tunable_int.value = "10"
    assert tunable_int.value == 10      # type: ignore[comparison-overlap]


def test_tunable_assign_str_to_float(tunable_float: Tunable) -> None:
    """
    Check str to float coercion.
    """
    tunable_float.value = "0.5"
    assert tunable_float.value == 0.5   # type: ignore[comparison-overlap]


def test_tunable_assign_float_to_int(tunable_int: Tunable) -> None:
    """
    Check float to int coercion.
    """
    tunable_int.value = 10.0
    assert tunable_int.value == 10


def test_tunable_assign_float_to_int_fail(tunable_int: Tunable) -> None:
    """
    Check the invalid float to int coercion.
    """
    with pytest.raises(ValueError):
        tunable_int.value = 10.1
