#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Functions to convert TunableGroups to ConfigSpace for use with the mlos_core optimizers.
"""

import logging

from typing import Dict, Optional

from ConfigSpace import (
    Configuration,
    ConfigurationSpace,
    CategoricalHyperparameter,
    UniformIntegerHyperparameter,
    UniformFloatHyperparameter,
    EqualsCondition,
)
from mlos_bench.tunables.tunable import Tunable, TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


def _tunable_to_configspace(
        tunable: Tunable, group_name: Optional[str] = None, cost: int = 0) -> ConfigurationSpace:
    """
    Convert a single Tunable to an equivalent ConfigSpace Hyperparameter objects,
    wrapped in a ConfigurationSpace for composability.

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
    cs : ConfigurationSpace
        A ConfigurationSpace object that corresponds to the Tunable.
    """
    meta = {"group": group_name, "cost": cost}  # {"scaling": ""}

    if tunable.type == "categorical":
        return ConfigurationSpace({
            tunable.name: CategoricalHyperparameter(
                name=tunable.name, choices=tunable.categories,
                default_value=tunable.default, meta=meta)
        })

    if tunable.type == "int":
        hp_type = UniformIntegerHyperparameter
    elif tunable.type == "float":
        hp_type = UniformFloatHyperparameter
    else:
        raise TypeError(f"Undefined Parameter Type: {tunable.type}")

    if not tunable.special:
        return ConfigurationSpace({
            tunable.name: hp_type(
                name=tunable.name, lower=tunable.range[0], upper=tunable.range[1],
                default_value=tunable.default if tunable.in_range(tunable.default) else None,
                meta=meta)
        })

    cs = ConfigurationSpace({
        "range": hp_type(
            name=tunable.name + ":range",
            lower=tunable.range[0], upper=tunable.range[1],
            default_value=tunable.default if tunable.in_range(tunable.default) else None,
            meta=meta),
        "special": CategoricalHyperparameter(
            name=tunable.name + ":special",
            choices=tunable.special,
            default_value=tunable.default if tunable.default in tunable.special else None,
            meta=meta),
        "type": CategoricalHyperparameter(
            name=tunable.name + ":type",
            choices=["special", "range"], default_value="special",
            weights=[0.1, 0.9]),  # TODO: Make weights configurable
    })

    cs.add_condition(EqualsCondition(
        cs[tunable.name + ":special"], cs[tunable.name + ":type"], "special"))
    cs.add_condition(EqualsCondition(
        cs[tunable.name + ":range"], cs[tunable.name + ":type"], "range"))

    return cs


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
    for (tunable, group) in tunables:
        space.add_configuration_space(
            prefix="", delimiter="",
            configuration_space=_tunable_to_configspace(
                tunable, group.name, group.get_current_cost()))
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
    values: Dict[str, TunableValue] = {}
    for (tunable, _group) in tunables:
        if tunable.special:
            if tunable.value in tunable.special:
                values[tunable.name + ":type"] = "special"
                values[tunable.name + ":special"] = tunable.value
            else:
                values[tunable.name + ":type"] = "range"
                values[tunable.name + ":range"] = tunable.value
        else:
            values[tunable.name] = tunable.value
    configspace = tunable_groups_to_configspace(tunables)
    return Configuration(configspace, values=values)
