#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Functions to convert TunableGroups to ConfigSpace for use with the mlos_core optimizers.
"""

import logging

from typing import Optional

from ConfigSpace.hyperparameters import Hyperparameter
from ConfigSpace import UniformIntegerHyperparameter
from ConfigSpace import UniformFloatHyperparameter
from ConfigSpace import CategoricalHyperparameter
from ConfigSpace import ConfigurationSpace, Configuration

from mlos_bench.tunables.tunable import Tunable
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


def _tunable_to_hyperparameter(
        tunable: Tunable, group_name: Optional[str] = None, cost: int = 0) -> Hyperparameter:
    """
    Convert a single Tunable to an equivalent ConfigSpace Hyperparameter object.

    Parameters
    ----------
    tunable : Tunable
        An mlos_bench Tunable object.
    group_name : str
        Human-readable id of the CovariantTunableGroup this Tunable belongs to.
    cost : int
        Cost to change this parameter (comes from the corresponding CovariantTunableGroup).

    Returns
    -------
    hyperparameter : Hyperparameter
        A ConfigSpace Hyperparameter object that corresponds to the Tunable.
    """
    meta = {"group": group_name, "cost": cost}  # {"lower": "", "upper": "", "scaling": ""}
    if tunable.type == "categorical":
        return CategoricalHyperparameter(
            tunable.name, choices=tunable.categories,
            default_value=tunable.default, meta=meta)
    elif tunable.type == "int":
        return UniformIntegerHyperparameter(
            tunable.name, lower=tunable.range[0], upper=tunable.range[1],
            default_value=tunable.default, meta=meta)
    elif tunable.type == "float":
        return UniformFloatHyperparameter(
            tunable.name, lower=tunable.range[0], upper=tunable.range[1],
            default_value=tunable.default, meta=meta)
    else:
        raise TypeError(f"Undefined Parameter Type: {tunable.type}")


def tunable_groups_to_configspace(tunables: TunableGroups, seed: Optional[int] = None) -> ConfigurationSpace:
    """
    Convert TunableGroups to  hyperparameters in ConfigurationSpace.

    Parameters
    ----------
    tunables : TunableGroups
        A collection of tunable parameters.

    seed : Optional[int]
        Random seed to use.

    Returns
    -------
    configspace : ConfigurationSpace
        A new ConfigurationSpace instance that corresponds to the input TunableGroups.
    """
    space = ConfigurationSpace(seed=seed)
    space.add_hyperparameters([
        _tunable_to_hyperparameter(tunable, group.name, group.get_current_cost())
        for (tunable, group) in tunables
    ])
    return space


def tunable_values_to_configuration(tunables: TunableGroups) -> Configuration:
    """
    Converts a TunableGroups current values to a ConfigSpace Configuration.

    Parameters
    ----------
    tunables : TunableGroups
        The TunableGroups to take the current value from.

    Returns
    -------
    Configuration
        A ConfigSpace Configuration.
    """
    configspace = tunable_groups_to_configspace(tunables)
    return Configuration(configspace, values={tunable.name: tunable.value for (tunable, _group) in tunables})
