#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for converting tunable parameters with explicitly
specified distributions to ConfigSpace.
"""

from typing import Literal

import pytest

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.optimizers.convert_configspace import tunable_groups_to_configspace


@pytest.mark.parametrize("tunable_type", ["int", "float"])
@pytest.mark.parametrize("distr_name,distr_params", [
    ("normal", {"mu": 0, "std": 1.0}),
    ("beta", {"alpha": 2, "beta": 5}),
    ("uniform", {}),
])
def test_convert_numerical_distributions(tunable_type: str,
                                         distr_name: Literal['normal', 'uniform', 'beta'],
                                         distr_params: dict) -> None:
    """
    Convert a numerical Tunable with explicit distribution to ConfigSpace.
    """
    tunable_groups = TunableGroups({
        "tunable_group": {
            "cost": 1,
            "params": {
                "tunable_param": {
                    "type": tunable_type,
                    "range": [0, 10],
                    "special_values": [0],
                    "special_weights": [0.2],
                    "range_weight": 0.8,
                    "distribution": {
                        "type": distr_name,
                        "params": distr_params
                    },
                    "default": 0
                }
            }
        }
    })

    (tunable, _group) = tunable_groups.get_tunable("tunable_param")
    assert tunable.distribution == distr_name
    assert tunable.distribution_params == distr_params

    space = tunable_groups_to_configspace(tunable_groups)
    assert space is not None
