"""
Functions to convert TunableGroups to ConfigSpace for use with the mlos_core optimizers.
"""

import logging

from typing import List

from ConfigSpace.hyperparameters import Hyperparameter
from ConfigSpace import UniformIntegerHyperparameter
from ConfigSpace import UniformFloatHyperparameter
from ConfigSpace import CategoricalHyperparameter

from mlos_bench.environment import Tunable, TunableGroups

_LOG = logging.getLogger(__name__)

# pylint: disable=protected-access


def _tunable_to_hyperparameter(
        tunable: Tunable, group_name: str = None, cost: int = 0) -> Hyperparameter:
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
    if tunable._type == "categorical":
        return CategoricalHyperparameter(
            tunable._name, choices=tunable._values,
            default_value=tunable.value, meta=meta)
    elif tunable._type == "int":
        return UniformIntegerHyperparameter(
            tunable._name, lower=tunable._range[0], upper=tunable._range[1],
            default_value=tunable.value, meta=meta)
    elif tunable._type == "float":
        return UniformFloatHyperparameter(
            tunable._name, lower=tunable._range[0], upper=tunable._range[1],
            default_value=tunable.value, meta=meta)
    else:
        raise TypeError("Undefined Parameter Type: " + tunable._type)


def tunable_groups_to_configspace(tunables: TunableGroups) -> List[Hyperparameter]:
    """
    Convert TunableGroups to a list of ConfigSpace hyperparameters.

    Parameters
    ----------
    tunables : TunableGroups
        A collection of tunable parameters.

    Returns
    -------
    configspace : List[Hyperparameter]
        A list of ConfigSpace Hyperparameter objects.
    """
    return [_tunable_to_hyperparameter(tunable, group_name, group.get_cost())
            for (group_name, group) in tunables._tunable_groups.items()
            for tunable in group._tunables.values()]
