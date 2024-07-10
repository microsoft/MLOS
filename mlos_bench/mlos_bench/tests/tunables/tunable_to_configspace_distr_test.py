#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for converting tunable parameters with explicitly specified distributions
to ConfigSpace.
"""

import pytest
from ConfigSpace import (
    BetaFloatHyperparameter,
    BetaIntegerHyperparameter,
    CategoricalHyperparameter,
    NormalFloatHyperparameter,
    NormalIntegerHyperparameter,
    UniformFloatHyperparameter,
    UniformIntegerHyperparameter,
)

from mlos_bench.optimizers.convert_configspace import (
    special_param_names,
    tunable_groups_to_configspace,
)
from mlos_bench.tunables.tunable import DistributionName
from mlos_bench.tunables.tunable_groups import TunableGroups

_CS_HYPERPARAMETER = {
    ("float", "beta"): BetaFloatHyperparameter,
    ("int", "beta"): BetaIntegerHyperparameter,
    ("float", "normal"): NormalFloatHyperparameter,
    ("int", "normal"): NormalIntegerHyperparameter,
    ("float", "uniform"): UniformFloatHyperparameter,
    ("int", "uniform"): UniformIntegerHyperparameter,
}


@pytest.mark.parametrize("param_type", ["int", "float"])
@pytest.mark.parametrize(
    "distr_name,distr_params",
    [
        ("normal", {"mu": 0.0, "sigma": 1.0}),
        ("beta", {"alpha": 2, "beta": 5}),
        ("uniform", {}),
    ],
)
def test_convert_numerical_distributions(
    param_type: str,
    distr_name: DistributionName,
    distr_params: dict,
) -> None:
    """Convert a numerical Tunable with explicit distribution to ConfigSpace."""
    tunable_name = "x"
    tunable_groups = TunableGroups(
        {
            "tunable_group": {
                "cost": 1,
                "params": {
                    tunable_name: {
                        "type": param_type,
                        "range": [0, 100],
                        "special": [-1, 0],
                        "special_weights": [0.1, 0.2],
                        "range_weight": 0.7,
                        "distribution": {"type": distr_name, "params": distr_params},
                        "default": 0,
                    }
                },
            }
        }
    )

    (tunable, _group) = tunable_groups.get_tunable(tunable_name)
    assert tunable.distribution == distr_name
    assert tunable.distribution_params == distr_params

    space = tunable_groups_to_configspace(tunable_groups)

    (tunable_special, tunable_type) = special_param_names(tunable_name)
    assert set(space.keys()) == {tunable_name, tunable_type, tunable_special}

    assert isinstance(space[tunable_special], CategoricalHyperparameter)
    assert isinstance(space[tunable_type], CategoricalHyperparameter)

    cs_param = space[tunable_name]
    assert isinstance(cs_param, _CS_HYPERPARAMETER[param_type, distr_name])
    for key, val in distr_params.items():
        assert getattr(cs_param, key) == val
