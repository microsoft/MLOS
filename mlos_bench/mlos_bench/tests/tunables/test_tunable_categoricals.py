#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for deep copy of tunable objects and groups."""

from mlos_bench.tunables.tunable_groups import TunableGroups


def test_tunable_categorical_types() -> None:
    """Check if we accept tunable categoricals as ints as well as strings and convert
    both to strings.
    """
    tunable_params = {
        "test-group": {
            "cost": 1,
            "params": {
                "int-cat": {
                    "type": "categorical",
                    "values": [1, 2, 3],
                    "default": 1,
                },
                "bool-cat": {
                    "type": "categorical",
                    "values": [True, False],
                    "default": True,
                },
                "false-bool-cat": {
                    "type": "categorical",
                    "values": [True, False],
                    "default": False,
                },
                "str-cat": {
                    "type": "categorical",
                    "values": ["a", "b", "c"],
                    "default": "a",
                },
            },
        }
    }
    tunable_groups = TunableGroups(tunable_params)
    tunable_groups.reset()

    int_cat, _ = tunable_groups.get_tunable("int-cat")
    assert isinstance(int_cat.value, str)
    assert int_cat.value == "1"

    bool_cat, _ = tunable_groups.get_tunable("bool-cat")
    assert isinstance(bool_cat.value, str)
    assert bool_cat.value == "True"

    false_bool_cat, _ = tunable_groups.get_tunable("false-bool-cat")
    assert isinstance(false_bool_cat.value, str)
    assert false_bool_cat.value == "False"

    str_cat, _ = tunable_groups.get_tunable("str-cat")
    assert isinstance(str_cat.value, str)
    assert str_cat.value == "a"
