#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Functions to convert TunableGroups to ConfigSpace for use with the mlos_core optimizers.
"""

import logging

from typing import Dict, Optional, Tuple

from ConfigSpace import (
    CategoricalHyperparameter,
    Configuration,
    ConfigurationSpace,
    EqualsCondition,
    UniformFloatHyperparameter,
    UniformIntegerHyperparameter,
)
from mlos_bench.tunables.tunable import Tunable, TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class TunableValueKind:
    """
    Enum for the kind of the tunable value (special or not).
    It is not a true enum because ConfigSpace wants string values.
    """

    # pylint: disable=too-few-public-methods
    SPECIAL = "special"
    RANGE = "range"


def _tunable_to_configspace(
        tunable: Tunable, group_name: Optional[str] = None, cost: int = 0) -> ConfigurationSpace:
    """
    Convert a single Tunable to an equivalent set of ConfigSpace Hyperparameter objects,
    wrapped in a ConfigurationSpace for composability.
    Note: this may be more than one Hyperparameter in the case of special value handling.

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

    # Create three hyperparameters: one for regular values,
    # one for special values, and one to choose between the two.
    (special_name, type_name) = special_param_names(tunable.name)
    conf_space = ConfigurationSpace({
        tunable.name: hp_type(
            name=tunable.name, lower=tunable.range[0], upper=tunable.range[1],
            default_value=tunable.default if tunable.in_range(tunable.default) else None,
            meta=meta),
        special_name: CategoricalHyperparameter(
            name=special_name, choices=tunable.special,
            default_value=tunable.default if tunable.default in tunable.special else None,
            meta=meta),
        type_name: CategoricalHyperparameter(
            name=type_name,
            choices=[TunableValueKind.SPECIAL, TunableValueKind.RANGE],
            default_value=TunableValueKind.SPECIAL,
            weights=[0.5, 0.5]),  # TODO: Make weights configurable; FLAML requires uniform weights.
    })
    conf_space.add_condition(EqualsCondition(
        conf_space[special_name], conf_space[type_name], TunableValueKind.SPECIAL))
    conf_space.add_condition(EqualsCondition(
        conf_space[tunable.name], conf_space[type_name], TunableValueKind.RANGE))

    return conf_space


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
            (special_name, type_name) = special_param_names(tunable.name)
            if tunable.value in tunable.special:
                values[type_name] = TunableValueKind.SPECIAL
                values[special_name] = tunable.value
            else:
                values[type_name] = TunableValueKind.RANGE
                values[tunable.name] = tunable.value
        else:
            values[tunable.name] = tunable.value
    configspace = tunable_groups_to_configspace(tunables)
    return Configuration(configspace, values=values)


def configspace_data_to_tunable_values(data: dict) -> dict:
    """
    Remove the fields that correspond to special values in ConfigSpace.
    In particular, remove and keys suffixes added by `special_param_names`.
    """
    data = data.copy()
    specials = [
        special_param_name_strip(k)
        for k in data.keys() if special_param_name_is_temp(k)
    ]
    for k in specials:
        (special_name, type_name) = special_param_names(k)
        if data[type_name] == TunableValueKind.SPECIAL:
            data[k] = data[special_name]
        if special_name in data:
            del data[special_name]
        del data[type_name]
    return data


def special_param_names(name: str) -> Tuple[str, str]:
    """
    Generate the names of the auxiliary hyperparameters that correspond
    to a tunable that can have special values.

    NOTE: `!` characters are currently disallowed in Tunable names in order handle this logic.

    Parameters
    ----------
    name : str
        The name of the tunable parameter.

    Returns
    -------
    special_name : str
        The name of the hyperparameter that corresponds to the special value.
    type_name : str
        The name of the hyperparameter that chooses between the regular and the special values.
    """
    return (name + "!special", name + "!type")


def special_param_name_is_temp(name: str) -> bool:
    """
    Check if name corresponds to a temporary ConfigSpace parameter.

    NOTE: `!` characters are currently disallowed in Tunable names in order handle this logic.

    Parameters
    ----------
    name : str
        The name of the hyperparameter.

    Returns
    -------
    is_special : bool
        True if the name corresponds to a temporary ConfigSpace hyperparameter.
    """
    return name.endswith("!type")


def special_param_name_strip(name: str) -> str:
    """
    Remove the temporary suffix from a special parameter name.

    NOTE: `!` characters are currently disallowed in Tunable names in order handle this logic.

    Parameters
    ----------
    name : str
        The name of the hyperparameter.

    Returns
    -------
    stripped_name : str
        The name of the hyperparameter without the temporary suffix.
    """
    return name.split("!", 1)[0]
