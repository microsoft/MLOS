#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for deep copy of tunable objects and groups.
"""

from mlos_bench.tunables.tunable_groups import TunableGroups


def test_tunable_categorical_ints() -> None:
    """
    Check if we accept tunable categoricals as ints as well as strings.
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
                "str-cat": {
                    "type": "categorical",
                    "values": ["a", "b", "c"],
                    "default": "a",
                },
            }
        }
    }
    tunable_groups = TunableGroups(tunable_params)
    tunable_groups.reset()
    int_cat, _ = tunable_groups.get_tunable("int-cat")
    assert isinstance(int_cat.value, int)
    str_cat, _ = tunable_groups.get_tunable("str-cat")
    assert isinstance(str_cat.value, str)
