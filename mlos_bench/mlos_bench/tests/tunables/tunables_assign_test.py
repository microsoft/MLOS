#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for assigning values to the individual parameters within tunable
groups.
"""

import json5 as json
import pytest

from mlos_bench.tunables.tunable import Tunable
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_tunables_assign_unknown_param(tunable_groups: TunableGroups) -> None:
    """Make sure that bulk assignment fails for parameters that don't exist in the
    TunableGroups object.
    """
    with pytest.raises(KeyError):
        tunable_groups.assign(
            {
                "vmSize": "Standard_B2ms",
                "idle": "mwait",
                "UnknownParam_1": 1,
                "UnknownParam_2": "invalid-value",
            }
        )


def test_tunables_assign_categorical(tunable_categorical: Tunable) -> None:
    """Regular assignment for categorical tunable."""
    # Must be one of: {"Standard_B2s", "Standard_B2ms", "Standard_B4ms"}
    tunable_categorical.value = "Standard_B4ms"
    assert not tunable_categorical.is_special


def test_tunables_assign_invalid_categorical(tunable_groups: TunableGroups) -> None:
    """Check parameter validation for categorical tunables."""
    with pytest.raises(ValueError):
        tunable_groups.assign({"vmSize": "InvalidSize"})


def test_tunables_assign_invalid_range(tunable_groups: TunableGroups) -> None:
    """Check parameter out-of-range validation for numerical tunables."""
    with pytest.raises(ValueError):
        tunable_groups.assign({"kernel_sched_migration_cost_ns": -2})


def test_tunables_assign_coerce_str(tunable_groups: TunableGroups) -> None:
    """Check the conversion from strings when assigning to an integer parameter."""
    tunable_groups.assign({"kernel_sched_migration_cost_ns": "10000"})


def test_tunables_assign_coerce_str_range_check(tunable_groups: TunableGroups) -> None:
    """Check the range when assigning to an integer tunable."""
    with pytest.raises(ValueError):
        tunable_groups.assign({"kernel_sched_migration_cost_ns": "5500000"})


def test_tunables_assign_coerce_str_invalid(tunable_groups: TunableGroups) -> None:
    """Make sure we fail when assigning an invalid string to an integer tunable."""
    with pytest.raises(ValueError):
        tunable_groups.assign({"kernel_sched_migration_cost_ns": "1.1"})


def test_tunable_assign_str_to_numerical(tunable_int: Tunable) -> None:
    """Check str to int coercion."""
    with pytest.raises(ValueError):
        tunable_int.numerical_value = "foo"  # type: ignore[assignment]


def test_tunable_assign_int_to_numerical_value(tunable_int: Tunable) -> None:
    """Check numerical value assignment."""
    tunable_int.numerical_value = 10.0
    assert tunable_int.numerical_value == 10
    assert not tunable_int.is_special


def test_tunable_assign_float_to_numerical_value(tunable_float: Tunable) -> None:
    """Check numerical value assignment."""
    tunable_float.numerical_value = 0.1
    assert tunable_float.numerical_value == 0.1
    assert not tunable_float.is_special


def test_tunable_assign_str_to_int(tunable_int: Tunable) -> None:
    """Check str to int coercion."""
    tunable_int.value = "10"
    assert tunable_int.value == 10  # type: ignore[comparison-overlap]
    assert not tunable_int.is_special


def test_tunable_assign_str_to_float(tunable_float: Tunable) -> None:
    """Check str to float coercion."""
    tunable_float.value = "0.5"
    assert tunable_float.value == 0.5  # type: ignore[comparison-overlap]
    assert not tunable_float.is_special


def test_tunable_assign_float_to_int(tunable_int: Tunable) -> None:
    """Check float to int coercion."""
    tunable_int.value = 10.0
    assert tunable_int.value == 10
    assert not tunable_int.is_special


def test_tunable_assign_float_to_int_fail(tunable_int: Tunable) -> None:
    """Check the invalid float to int coercion."""
    with pytest.raises(ValueError):
        tunable_int.value = 10.1


def test_tunable_assign_null_to_categorical() -> None:
    """Checks that we can use null/None in categorical tunables."""
    json_config = """
    {
        "name": "categorical_test",
        "type": "categorical",
        "values": ["foo", null],
        "default": "foo"
    }
    """
    config = json.loads(json_config)
    categorical_tunable = Tunable(name="categorical_test", config=config)
    assert categorical_tunable
    assert categorical_tunable.category == "foo"
    categorical_tunable.value = None
    assert categorical_tunable.value is None
    assert categorical_tunable.value != "None"
    assert categorical_tunable.category is None


def test_tunable_assign_null_to_int(tunable_int: Tunable) -> None:
    """Checks that we can't use null/None in integer tunables."""
    with pytest.raises((TypeError, AssertionError)):
        tunable_int.value = None
    with pytest.raises((TypeError, AssertionError)):
        tunable_int.numerical_value = None  # type: ignore[assignment]


def test_tunable_assign_null_to_float(tunable_float: Tunable) -> None:
    """Checks that we can't use null/None in float tunables."""
    with pytest.raises((TypeError, AssertionError)):
        tunable_float.value = None
    with pytest.raises((TypeError, AssertionError)):
        tunable_float.numerical_value = None  # type: ignore[assignment]


def test_tunable_assign_special(tunable_int: Tunable) -> None:
    """Check the assignment of a special value outside of the range (but declared
    `special`).
    """
    tunable_int.numerical_value = -1
    assert tunable_int.numerical_value == -1
    assert tunable_int.is_special


def test_tunable_assign_special_fail(tunable_int: Tunable) -> None:
    """Assign a value that is neither special nor in range and fail."""
    with pytest.raises(ValueError):
        tunable_int.numerical_value = -2


def test_tunable_assign_special_with_coercion(tunable_int: Tunable) -> None:
    """
    Check the assignment of a special value outside of the range (but declared
    `special`).

    Check coercion from float to int.
    """
    tunable_int.numerical_value = -1.0
    assert tunable_int.numerical_value == -1
    assert tunable_int.is_special


def test_tunable_assign_special_with_coercion_str(tunable_int: Tunable) -> None:
    """
    Check the assignment of a special value outside of the range (but declared
    `special`).

    Check coercion from string to int.
    """
    tunable_int.value = "-1"
    assert tunable_int.numerical_value == -1
    assert tunable_int.is_special
